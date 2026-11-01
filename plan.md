# Plano — Nexo Estoque: login individual por nome de usuário

## Objetivo e decisão de acesso

Manter contas individuais e criação exclusiva por administradores, mas trocar o identificador do login de e-mail para nome de usuário único. A conta solicitada usa `Turma2` como username; o valor será normalizado sem diferenciar maiúsculas/minúsculas. O usuário definirá a própria senha no formulário protegido de primeiro acesso; a senha deve ter pelo menos 12 caracteres e não será colocada no código, em arquivo de configuração, ZIP, log ou mensagem. Não existe cadastro público, autoinscrição nem fluxo de convite. O primeiro administrador continua sendo criado somente por bootstrap de uso único protegido por `NEXO_ADMIN_BOOTSTRAP_KEY`; depois do primeiro admin ativo, o bootstrap fecha. E-mail passa a ser opcional e não é usado para autenticar.

O backend valida username ASCII único (3–32 caracteres, letras, números, ponto, sublinhado e hífen) e o armazena normalizado em minúsculas; o login aceita `Turma2` em qualquer capitalização. Senhas continuam em hash scrypt da biblioteca padrão, com salt e parâmetros verificáveis. A sessão permanece JWT HS256 com expiração, assinada por `NEXO_SESSION_SECRET`, distinto da chave de bootstrap. O cookie é `HttpOnly`, `SameSite=None; Secure` no Preview HTTPS e tem política compatível com HTTP local. Mutações exigem a marca de requisição de mesma origem e todas as autorizações/estados são verificados no servidor.

Para impedir bootstrap e alterações administrativas concorrentes, criação/edição/desativação de contas e bootstrap usam a mesma trava transacional na linha v4 de `schema_migrations`; o ator é revalidado após obter o lock e a contagem de admins usa leitura bloqueante até o commit. O último administrador ativo não pode ser desativado nem rebaixado. Login por username e resolução de sessões também falham com HTTP 503 se a v4 não estiver aplicada.

## Migração e preservação dos dados

A migração v3 já aplicada adiciona username e índice único sem apagar tabelas nem histórico. Para contas existentes, ela deriva usernames únicos do local-part do e-mail (ou nome, quando não houver e-mail), normaliza o valor e acrescenta sufixos determinísticos em caso de colisão. A v4 adiciona a restrição `NOT NULL` em MySQL e, nos testes SQLite, triggers equivalentes para inserção/atualização; ela verifica o backfill e não apaga linhas. A coluna de e-mail e seu índice são preservados; novos usuários podem omitir e-mail. Migrações v1/v2/v3 continuam em sequência, v4 é repetível e todos os endpoints de username exigem o marcador v4. Contas legadas sem senha individual seguem inativas até reivindicação protegida no bootstrap, preservando identificador e trilha de auditoria.

O banco gerenciado é compartilhado entre Preview e produção; portanto, a migração é aditiva e não apaga/sobrescreve usuários, produtos ou movimentações. Catálogo, ledger, saldos, alertas, previsões, integração RFID e materiais Wokwi permanecem funcionais.

## Integração da aplicação

- **API e sessão:** atualizar `POST /api/auth/login` para receber username/senha; manter status da sessão, bootstrap condicional e logout. O bootstrap recebe nome, username, senha, chave protegida e e-mail opcional.
- **Contas:** CRUD administrativo recebe username obrigatório e e-mail opcional; usernames são únicos e insensíveis a maiúsculas/minúsculas. Preservar perfis `admin`/`operador`, redefinição de senha, desativação lógica e o bloqueio do último admin.
- **Interface:** atualizar `Login.tsx` para o campo “Usuário” e aceitar `Turma2`; pré-preencher `Turma2` no formulário inicial do admin, sem pré-preencher senha; tornar e-mail opcional em `PrimeiroAcesso.tsx` e `Usuarios.tsx`; manter a rota de usuários protegida e o link somente para admin.
- **Segredos/ambiente:** usar somente `NEXO_SESSION_SECRET` e `NEXO_ADMIN_BOOTSTRAP_KEY` via configuração protegida; manter valores reais fora de Git, Docker e ZIP.

## Estrutura relevante do projeto

- `frontend/src/pages/Login.tsx` e `PrimeiroAcesso.tsx`: login por username e bootstrap condicional, com senha digitada pela pessoa.
- `frontend/src/pages/Usuarios.tsx`, `App.tsx`, `components/Sidebar.tsx`, `components/Header.tsx`, `services/api.ts` e `types/index.ts`: gestão admin, guards, navegação e contratos.
- `backend/app/models/usuario.py`, `schemas/auth.py`, `services/auth_service.py`, `routes/auth.py` e `routes/usuarios.py`: usernames, hashing, sessão e autorização.
- `backend/app/database/migrations/v0003_username_login.py`, `v0004_username_not_null.py` e `database/tables.py`: backfill aditivo, unicidade, integridade NOT NULL e execução versionada.
- `backend/tests/`: cobertura isolada de login, bootstrap, permissões, unicidade/normalização e migrações.
- `frontend/public/manus-routes.json`, `README.md`, `backend/.env.example` e `TODO.md`: rotas e documentação sincronizadas.
- `wokwi/`, `docs/` e serviços de estoque, RFID e previsões: preservar comportamento existente.

## Design preservado

- **Movimento:** painel operacional industrial/técnico, inspirado em instrumentação de inventário e sinalização de chão de fábrica.
- **Princípios centrais:** leitura rápida; hierarquia voltada à operação; estados explícitos e acessíveis; precisão visual sem ornamento gratuito.
- **Filosofia de cor:** navegação e contexto técnico em grafite, superfícies claras para leitura prolongada, verde-mint para fluxo positivo e âmbar/vermelho reservados a atenção e ruptura.
- **Paradigma de layout:** navegação lateral fixa no desktop e gaveta no celular; conteúdo segue o fluxo de trabalho do estoque; autenticação em composição dividida, com contexto técnico à esquerda e formulário compacto à direita.
- **Elementos de assinatura:** monograma geométrico verde; linhas de grade técnicas discretas; rótulos monoespaçados para dados operacionais.
- **Filosofia de interação:** respostas imediatas com carregamento, confirmação e erro legíveis; ações administrativas deixam papel e estado explícitos; desativação lógica preserva a auditoria.
- **Animação:** transições curtas e discretas, em torno de 150–200 ms, para foco, modal e feedback; evitar movimento contínuo que distraia.
- **Tipografia:** DM Sans para leitura e interface; IBM Plex Mono para identificadores, RFID e métricas; títulos compactos e números tabulares.
- **Essência da marca:** controle de inventário claro para equipes que precisam antecipar ruptura e rastrear cada mudança. Personalidade: técnica, confiável e objetiva.
- **Voz:** direta e operacional. Exemplos: “Entre na operação.” e “Cada movimentação tem responsável e histórico.”
- **Marca/logotipo:** manter o monograma geométrico “N” existente, sem recriar ou substituir o ativo de marca.
- **Cor proprietária:** verde-mint `#32c48d`, reservado para fluxo positivo e ações primárias.
