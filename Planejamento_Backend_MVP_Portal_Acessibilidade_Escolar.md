# Planejamento do Backend — MVP enxuto
*Portal de Acessibilidade Escolar · FastAPI + SQLAlchemy 2.0 + SQLite · piloto na região metropolitana do Recife*

Esta versão substitui o planejamento anterior no que diz respeito aos dados. A arquitetura foi mantida.

## 0. O que mudou em relação à versão anterior

- **Banco**: SQLite (sem PostGIS, pg_trgm, GIN, colunas geradas).
- **Dados enxutos**: de 12 tabelas para 7. Saíram `municipalities`, `accessibility_categories` (agora enum), `review_forms`, `review_questions`, `snapshots` e `staff_users`.
- **Formulário em enums** (grupos e subgrupos) no lugar de tabelas de perguntas.
- **Usuários**: qualquer pessoa pode criar conta; avaliação anônima continua existindo. Avaliações de usuários cadastrados aparecem primeiro na listagem de avaliações da escola, mas **todas contam igual na média**.
- **Mapa**: segundo plano. As colunas de latitude e longitude já existem (opcionais), mas não há endpoint nem índice geográfico até a fase final.
- **Cadastro-semente**: por planilha CSV com script de importação, não por migration.
- **Paginação**: `limit/offset` simples (volume pequeno no piloto).

### Confirmado

- **Grupo = categoria macro do filtro.** "Mobilidade" equivale a "motora"; os subgrupos são os itens avaliados dentro do grupo (rampas, banheiro acessível etc.).
- **Prioridade de avaliações de usuários** é só de ordenação na consulta. Não altera a média.
- **Piso tátil** fica no grupo Visual.

### Suposições que fiz (confirme ou corrija)

1. **Escala de nota provisória de 1 a 5** (a mesma usada no protótipo de design). Fica numa constante e é fácil de trocar.
2. **Presença = existir linha.** Escola com linha em `school_groups` tem o grupo; sem linha, "não tem ou não informado". Isso simplifica o "sim/não" do RF05.
3. **Uma avaliação por usuário, por escola e por grupo.** Avaliações anônimas não têm essa trava.

---

## 1. Arquitetura (mantida)

Já temos o padrão arquitetural definido através das pastas do projeto. Deve-se criar pastas de apoio para abrigar os enums que irão aparecer nos modelos.

---

## 2. Enums: grupos e subgrupos

Proposta de pré-definição (valide com alguém da área de educação inclusiva antes de fixar). São 5 grupos com 4 subgrupos cada.

| Grupo | Subgrupos |
|---|---|
| **Mobilidade** | Rampas · Banheiro acessível · Elevador ou plataforma · Circulação interna (corredores, portas, pátio) |
| **Visual** | Piso tátil · Sinalização em braille e contraste · Material em braille ou ampliado · Tecnologia assistiva |
| **Auditiva** | Intérprete de Libras · Comunicação em Libras pela equipe · Alertas visuais · Recursos visuais e legendas |
| **Intelectual** | Apoio pedagógico individualizado · Material adaptado · Profissional de apoio · Flexibilização curricular |
| **TEA** | Espaço sensorial ou de acolhimento · Comunicação visual e rotina · Profissional de apoio · Formação da equipe |

```python
# app/models/enums.py
import enum

class Grupo(str, enum.Enum):
    MOBILIDADE = "mobilidade"
    VISUAL = "visual"
    AUDITIVA = "auditiva"
    INTELECTUAL = "intelectual"
    TEA = "tea"

class Subgrupo(str, enum.Enum):
    # mobilidade
    RAMPAS = "mobilidade.rampas"
    BANHEIRO_ACESSIVEL = "mobilidade.banheiro_acessivel"
    ELEVADOR_OU_PLATAFORMA = "mobilidade.elevador_ou_plataforma"
    CIRCULACAO_INTERNA = "mobilidade.circulacao_interna"
    # visual
    PISO_TATIL = "visual.piso_tatil"
    SINALIZACAO_BRAILLE_CONTRASTE = "visual.sinalizacao_braille_contraste"
    MATERIAL_BRAILLE_AMPLIADO = "visual.material_braille_ampliado"
    TECNOLOGIA_ASSISTIVA = "visual.tecnologia_assistiva"
    # auditiva
    INTERPRETE_LIBRAS = "auditiva.interprete_libras"
    COMUNICACAO_LIBRAS_EQUIPE = "auditiva.comunicacao_libras_equipe"
    ALERTAS_VISUAIS = "auditiva.alertas_visuais"
    RECURSOS_VISUAIS_LEGENDAS = "auditiva.recursos_visuais_legendas"
    # intelectual
    APOIO_PEDAGOGICO_INDIVIDUALIZADO = "intelectual.apoio_pedagogico_individualizado"
    MATERIAL_ADAPTADO = "intelectual.material_adaptado"
    PROFISSIONAL_APOIO_INTELECTUAL = "intelectual.profissional_apoio"
    FLEXIBILIZACAO_CURRICULAR = "intelectual.flexibilizacao_curricular"
    # tea
    ESPACO_SENSORIAL = "tea.espaco_sensorial"
    COMUNICACAO_VISUAL_ROTINA = "tea.comunicacao_visual_rotina"
    PROFISSIONAL_APOIO_TEA = "tea.profissional_apoio"
    FORMACAO_EQUIPE_TEA = "tea.formacao_equipe"

    @property
    def grupo(self) -> Grupo:
        return Grupo(self.value.split(".")[0])

SUBGRUPOS_POR_GRUPO = {g: [s for s in Subgrupo if s.grupo == g] for g in Grupo}
NOTA_MIN, NOTA_MAX = 1, 5  # provisório
```

Notas sobre o uso de enum no SQLite:

- SQLite não tem tipo enum nativo. Use `Enum(Grupo, native_enum=False, values_callable=lambda e: [m.value for m in e])` para guardar o **valor** como texto (e não o nome do membro do Python).
- O prefixo do subgrupo (`mobilidade.`) deixa o vínculo com o grupo explícito. O banco não valida isso sozinho: a regra "o subgrupo pertence ao grupo da avaliação" vai no `review_service` e em teste.
- Adicionar um subgrupo é mudança de código. Aceitável no MVP. Alterar o texto de perguntas antigas pode distorcer médias históricas, por isso `reviews.form_version` (abaixo).

---

## 3. Modelo de dados (7 tabelas)

| Tabela | Campos | Observações |
|---|---|---|
| `neighborhoods` | id, name, municipality (texto) | Único em (name, municipality). O município é texto porque nomes de bairro se repetem entre cidades ("Centro") |
| `schools` | id, name, name_normalized, neighborhood_id, address (opc.), **latitude (opc.), longitude (opc.)**, is_active, created_at | Único em (name_normalized, neighborhood_id). Lat/lng ficam nulos até a fase do mapa |
| `school_groups` | school_id, group | PK composta. Existir linha = a escola tem esse grupo de adaptação |
| `users` | id, email (único), password_hash, created_at | Só o necessário. E-mail é dado pessoal: nunca devolver em resposta pública |
| `reviews` | id, school_id, group, user_id (nulo), score, form_version, is_hidden, created_at | `score` = média das respostas. `user_id` nulo = anônima. `is_hidden` permite ocultar abuso sem apagar |
| `review_answers` | review_id, subgroup, value | PK (review_id, subgroup). `CHECK (value BETWEEN 1 AND 5)` |
| `school_group_stats` | school_id, group, review_count, score_sum | PK (school_id, group). Soma e contagem de **todas** as avaliações (anônimas ou não) |

```python
class School(Base):
    __tablename__ = "schools"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    name_normalized: Mapped[str] = mapped_column(String(200))   # minúsculas, sem acento
    neighborhood_id: Mapped[int] = mapped_column(ForeignKey("neighborhoods.id"), index=True)
    address: Mapped[str | None] = mapped_column(String(300))
    latitude: Mapped[float | None]      # reservado para o mapa
    longitude: Mapped[float | None]     # reservado para o mapa
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (UniqueConstraint("name_normalized", "neighborhood_id"),)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"), index=True)
    group: Mapped[Grupo] = mapped_column(Enum(Grupo, native_enum=False,
                                              values_callable=lambda e: [m.value for m in e]))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    score: Mapped[float]
    form_version: Mapped[int] = mapped_column(default=1)
    is_hidden: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    __table_args__ = (
        Index("uq_review_user_school_group", "user_id", "school_id", "group",
              unique=True, sqlite_where=text("user_id IS NOT NULL")),
    )
```

### Cuidados específicos do SQLite

- **Ative as chaves estrangeiras**: no SQLite elas ficam desligadas por padrão. No evento `connect` do engine, execute `PRAGMA foreign_keys=ON`.
- **Modo WAL** (`PRAGMA journal_mode=WAL`) e `busy_timeout` ajudam leitura e escrita concorrentes. Mesmo assim existe um único escritor por vez, o que atende bem o MVP. Se o tráfego crescer, a migração para PostgreSQL é o caminho natural, e o SQLAlchemy facilita isso.
- Com SQLite, prefira SQLAlchemy **síncrono** no MVP: o FastAPI executa rotas síncronas em threads, e você evita a complexidade do modo assíncrono. Use `check_same_thread=False` na conexão.
- Upsert nativo: `sqlalchemy.dialects.sqlite.insert(...).on_conflict_do_update(...)`.

---

## 4. Usuários e avaliações

- **Cadastro e login**: `POST /auth/register` e `POST /auth/login`, com hash de senha forte (Argon2 ou bcrypt, nunca texto puro) e token JWT.
- **Avaliar**: o token é **opcional** em `POST /schools/{id}/reviews`. Com token, grava `user_id`; sem token, a avaliação é anônima.
- **Corpo da avaliação**: `{ "group": "mobilidade", "form_version": 1, "answers": [{"subgroup": "mobilidade.rampas", "value": 4}, ...] }`. O usuário pode pular subgrupos que não sabe responder. Exige pelo menos uma resposta.
- **Validações** (no `review_service`): todos os subgrupos pertencem ao grupo informado; valores entre `NOTA_MIN` e `NOTA_MAX`; sem subgrupo repetido.
- **Prioridade para avaliações de usuários**: vale só para a **ordem da listagem** de avaliações da escola (seção 4.1). A média continua contando todas as avaliações igualmente.
- **Privacidade**: nunca expor e-mail nem `user_id` na API pública. Decisão sobre exclusão de conta e seus efeitos nas médias fica para depois.

### 4.1 Listagem de avaliações de uma escola

`GET /schools/{id}/reviews?group=mobilidade&limit=20&offset=0`

Ordem: avaliações de usuários cadastrados primeiro, depois as anônimas, e dentro de cada bloco as mais recentes primeiro.

```sql
SELECT r.id, r."group", r.score, r.created_at, (r.user_id IS NOT NULL) AS from_registered_user
FROM reviews r
WHERE r.school_id = :school AND r."group" = :group AND r.is_hidden = 0
ORDER BY (r.user_id IS NULL) ASC, r.created_at DESC, r.id DESC
LIMIT :limit OFFSET :offset;
```

- Cada item devolve grupo, nota, respostas por subgrupo e data. **Nunca** devolve `user_id` nem e-mail.
- O campo booleano `from_registered_user` é opcional: serve se o frontend quiser mostrar um indicador. Se não quiser, basta omitir; a ordem já resolve a prioridade.
- Como as anônimas contam normalmente na média, a prioridade não protege a média contra spam. Os controles de abuso (limite de taxa, validações) continuam necessários.

---

## 5. Cadastro-semente: planilha CSV + script

**Escolha: CSV com script de importação idempotente**, e não migration.

Por quê: migrations versionam a estrutura do banco. Dados de escolas vão mudar várias vezes conforme a equipe cadastra mais, e uma migration de dados é ruim de reexecutar e de corrigir. O script pode rodar quantas vezes for preciso sem duplicar.

```
nome,bairro,municipio,endereco,latitude,longitude,grupos
Escola Exemplo A,Boa Viagem,Recife,Rua X 100,,,mobilidade|visual
Escola Exemplo B,Várzea,Recife,,,,auditiva
```

`python -m app.scripts.import_schools schools.csv`

- Cria bairros e escolas ainda inexistentes; localiza a escola por (nome normalizado, bairro) e atualiza os campos.
- `grupos` aceita só valores do enum `Grupo` e rejeita o resto com mensagem clara.
- Latitude e longitude são opcionais. Linhas inválidas vão para um relatório de erros, sem derrubar a importação.
- As categorias (grupos e subgrupos) não precisam de seed: estão no código.

---

## 6. Endpoints do MVP

| Método | Rota | Função |
|---|---|---|
| GET | `/form` | Grupos e subgrupos (estrutura do formulário), escala e versão |
| GET | `/neighborhoods` | Bairros para o filtro |
| GET | `/schools` | Busca e filtro (`neighborhood_id`, `groups`, texto), ordenação e paginação |
| GET | `/schools/{id}` | Perfil: grupos presentes, média e contagem por grupo |
| GET | `/schools/{id}/reviews` | Lista avaliações da escola (usuários cadastrados primeiro) |
| POST | `/schools/{id}/reviews` | Envia avaliação (token opcional) |
| POST | `/auth/register`, `/auth/login` | Conta de usuário |

Fora do MVP: endpoints de administração. A equipe cadastra pelo script e modera direto no banco ou por script.

---

## 7. Filtro: OR com prioridade para quem tem todos os grupos

Regra: o filtro por vários grupos é OR (a escola entra se tiver pelo menos um), mas as escolas que têm **mais** dos grupos escolhidos aparecem primeiro, e quem tem todos vem no topo.

```sql
SELECT s.id, s.name,
       COUNT(sg.group)                              AS matched,
       SUM(st.score_sum) * 1.0 / NULLIF(SUM(st.review_count), 0) AS avg_score
FROM schools s
JOIN school_groups sg
  ON sg.school_id = s.id AND sg."group" IN (:g1, :g2)
LEFT JOIN school_group_stats st
  ON st.school_id = s.id AND st."group" IN (:g1, :g2)
WHERE s.neighborhood_id = :bairro AND s.is_active = 1
GROUP BY s.id
ORDER BY matched DESC, avg_score DESC NULLS LAST, s.id
LIMIT :limit OFFSET :offset;
```

Observação: com dois `JOIN` sobre as mesmas escolas, a soma das estatísticas pode ser multiplicada pelo número de linhas de `school_groups`. Em SQLAlchemy, vale calcular `matched` e `avg_score` em subqueries separadas e juntar por `school_id`, e conferir com um teste que usa uma escola com 2 grupos. O `NULLS LAST` exige SQLite 3.30 ou superior.

Ao exibir a média, aplique `MIN_REVIEWS_TO_DISPLAY` (valor a definir): abaixo disso, a API devolve só a contagem, sem média.

---

## 8. Otimização para o MVP (SQLite)

- **Índices úteis**: `schools(neighborhood_id)`, PK `(school_id, group)` em `school_groups` mais um índice `(group, school_id)`, PK em `school_group_stats`, e `reviews(school_id, group, created_at)` para a listagem de avaliações.
- Use `EXPLAIN QUERY PLAN` nas queries de listagem e rode `ANALYZE` depois de importações grandes.
- **Médias**: listagem lê `school_group_stats`, nunca `AVG()` sobre `reviews`. A gravação da avaliação e a atualização das estatísticas acontecem na **mesma transação**, via upsert.
- Busca por nome: `LIKE` sobre `name_normalized`. Para o volume do piloto basta. Se ficar lento, o SQLite tem FTS5.
- Evite N+1 com `selectinload` e devolva schemas enxutos na listagem.
- Cache simples em memória (TTL) para `/form` e `/neighborhoods`, que quase não mudam.

---

## 9. Mapa (segundo plano)

Já preparado nos dados: `latitude` e `longitude` opcionais em `schools`. Nada além disso por enquanto.

Quando chegar a vez (última fase, se houver tempo):

1. Preencher coordenadas das escolas (planilha da equipe ou geocodificação; confira os termos do serviço escolhido).
2. Índice em `(latitude, longitude)` e endpoint `GET /schools/map?bbox=...&groups=...` devolvendo GeoJSON enxuto.
3. Mapa montado no frontend (Maps JavaScript API, decisão já tomada na versão anterior), com clusterização no cliente.

---

## 10. Roadmap

| Fase | Entrega |
|---|---|
| 0. Preparação | Repositório, FastAPI, SQLAlchemy síncrono com SQLite (PRAGMAs), Alembic, pytest, CI |
| 1. Dados | Enums, models, migration inicial, script de importação do CSV |
| 2. Leitura | `/form`, `/neighborhoods`, `/schools` (filtro OR com prioridade), perfil da escola |
| 3. Escrita | Cadastro e login, `POST` de avaliação (anônima ou com usuário), estatísticas por upsert, listagem de avaliações com usuários primeiro |
| 4. Qualidade | Testes (filtro, estatísticas, validação de subgrupo, regra do mínimo de avaliações), limite de taxa, CORS, termo de uso |
| 5. Mapa (se der tempo) | Coordenadas, endpoint de mapa, integração no frontend |
| 6. Depois do MVP | Snapshots periódicos, relatórios, moderação, contas de equipe, selo institucional |
