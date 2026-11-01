# Banco de dados

## Entidades

- **produtos:** SKU único, nome, categoria, unidade, custo opcional, mínimo, saldo inicial, UID RFID opcional única, estado ativo, marca de demonstração e data de atualização.
- **movimentacoes:** produto, tipo (`entrada`, `saida`, `ajuste`), quantidade, motivo, openId/nome de quem registrou, origem (`manual`, `rfid`, `demonstracao`) e data. Índices por produto/data e data geral; remoção física em cascata não é usada pela aplicação.
- **usuarios:** `open_id` como chave, nome, username único, normalizado e obrigatório (3–32 caracteres), e-mail opcional com índice único quando informado, perfil (`admin` ou `operador`), hash de senha scrypt, estado ativo e data de criação. A senha em texto não é persistida. Login usa username; e-mail não é identificador de acesso.
- **schema_migrations:** versão aplicada e descrição. v1 cria as tabelas; v2 adiciona hash/estado e unicidade de e-mail; v3 acrescenta e preenche usernames únicos; v4 impõe `NOT NULL` em MySQL e triggers equivalentes para SQLite. Login, resolução de sessão, administração e bootstrap exigem o marcador v4; alterações administrativas compartilham lock transacional nessa linha.

## Regra

`saldo_atual = estoque_inicial + Σ(entradas) − Σ(saídas) + Σ(ajustes assinados)`.
Entradas e saídas são quantidades estritamente positivas; o backend converte saídas em delta negativo. Ajustes aceitam inteiro positivo ou negativo, nunca zero. O banco não armazena uma coluna de saldo como fonte de verdade; saldos apresentados são derivados do ledger.

## Inicialização e autenticação

A primeira migração cria tabelas ausentes com `metadata.create_all`, grava a versão e carrega catálogo/movimentos demonstrativos somente se a tabela de produtos estiver vazia. Migrações posteriores são aditivas e repetíveis; v3 deriva username do e-mail existente ou do nome, resolve colisões com sufixo e mantém e-mail, contas e movimentos sem exclusões; v4 só prossegue quando o backfill está completo. Contas antigas sem hash individual permanecem inativas até reivindicação segura no bootstrap. Para a primeira conta, o usuário pode confirmar `Turma2` e definir uma senha com pelo menos 12 caracteres no formulário protegido; não existe semeadura de credenciais padrão.

A URL MySQL é lida de `DATABASE_URL` no servidor. Segredos e arquivos `.env` não entram no frontend nem no Git. Desenvolvimento gerenciado e publicação podem compartilhar o mesmo banco; trate migrações e gravações de desenvolvimento como persistentes.
