# Nexo Estoque — controle inteligente de inventário

MVP web em português brasileiro para catálogo de produtos, entradas/saídas/ajustes rastreáveis, saldos, alertas, consumo histórico, previsões simples e leitura RFID simulada. Frontend React + TypeScript + Vite; API Python + FastAPI; SQLAlchemy sobre MySQL compatível gerenciado; contas individuais com login por username e criação exclusiva por administradores, sem cadastro público.

## Estrutura principal

- `frontend/`: aplicação React e manifesto `public/manus-routes.json`.
- `backend/app/`: API, modelos, schemas, autenticação individual, gestão administrativa, regras de saldo, RFID e previsões.
- `wokwi/`: diagrama ESP32 + RC522 + OLED e sketch de leitura serial.
- `docs/arquitetura/` e `docs/banco/`: arquitetura, persistência, migrações e regras do ledger.
- `Dockerfile`: build multi-stage; o container final atende API e arquivos React pelo mesmo listener.

## Desenvolvimento

Requisitos: Python 3.12, Node 22 e npm 10. O banco é injetado no runtime gerenciado. Para configuração local, copie `backend/.env.example` para `backend/.env`, configure `DATABASE_URL` e gere valores aleatórios independentes de pelo menos 32 bytes para `NEXO_SESSION_SECRET` e `NEXO_ADMIN_BOOTSTRAP_KEY`; `.gitignore` exclui o arquivo do Git e `.dockerignore` impede que ele entre no contexto de builds de imagem. No WebDev, configure esses valores pelo formulário protegido de secrets, nunca em arquivos versionados ou no chat.

Para gerar cada segredo localmente, execute o comando a seguir duas vezes e atribua cada saída a uma variável diferente. Nunca cole esses valores em conversas ou em arquivos versionados.

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

```bash
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm ci

# Terminal 1: API. DATABASE_URL precisa apontar para um MySQL compatível.
PYTHONPATH=backend .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2: frontend; o Vite encaminha /api e /_app para a API.
npm run dev
```

No workspace WebDev, o Preview é servido na porta configurada (3000). O primeiro startup cria somente tabelas ausentes, registra as versões de esquema e carrega exemplos **uma única vez**, somente se o catálogo estiver vazio. Alterações futuras não substituem produtos ou movimentos existentes. Os exemplos ficam identificados como demonstrativos; um produto criado pelo usuário não recebe essa marca.

## Uso

1. No primeiro acesso, use **Configurar o primeiro administrador** somente enquanto o backend indicar que o bootstrap está disponível; informe a chave de bootstrap definida no servidor, confirme o nome de usuário `Turma2` (ou escolha outro), digite uma senha própria com pelo menos 12 caracteres e, se desejar, informe e-mail. A tela cria a primeira conta como administradora e se fecha depois do sucesso. Não há cadastro público nem por convite; somente administradores autenticados criam contas em **Usuários**.
2. No login normal, entre com o nome de usuário individual e a senha; não é necessário e-mail.
3. Cadastre produtos em **Produtos**, informando SKU, mínimo e saldo inicial; UID RFID é opcional.
4. Registre entradas, saídas ou ajustes em **Movimentações**. Ajuste aceita quantidade positiva ou negativa; o backend bloqueia saldo final negativo.
5. Consulte o saldo calculado em **Estoque**, alertas por mínimo em **Alertas** e estimativas em **Previsões**.
6. Para a demonstração RFID, cadastre no produto a UID impressa pelo RC522. Digite essa mesma UID na caixa de leitura da página Movimentações; a leitura simulada registra o evento no mesmo livro.

## Banco e migrações

`DATABASE_URL` é lida exclusivamente pelo backend. `backend/app/database/tables.py` executa migrações aditivas e versionadas: a v2 adiciona hash/estado individual; a v3 preenche usernames únicos para as contas existentes, preserva e-mails e histórico, e permite e-mail opcional para novas contas; a v4 torna username obrigatório e bloqueia login, sessões e administração se o marcador final não estiver disponível. Em MySQL, username fica fisicamente `NOT NULL`; os testes SQLite têm triggers equivalentes para inserts/updates. Não há `DROP` nem reset automático. Contas legadas sem senha própria ficam inativas e podem ser reivindicadas no bootstrap protegido quando o username ou e-mail corresponder; nenhum usuário, produto ou movimento é apagado. O saldo é sempre `estoque_inicial + entradas - saídas + ajustes`; movimentações são preservadas como trilha de auditoria. A configuração gerenciada de desenvolvimento e publicação aponta ao banco do projeto, portanto alterações de esquema e dados nesse ambiente são persistentes.

## Previsões

O serviço usa a série dos últimos 30 dias. Com pelo menos cinco dias distintos de saída, combina uma tendência linear leve com média diária; com amostra menor, usa média conservadora e marca a confiança como limitada; sem consumo, exibe “sem histórico suficiente”. Use **Recalcular modelos** ou execute:

```bash
PYTHONPATH=backend .venv/bin/python -m app.ml.treinamento
```

O treinamento grava `backend/app/ml/modelo.pkl`; esse artefato é reproduzível a partir do banco e por isso é ignorado no Git. Sem histórico real, as previsões não devem ser usadas como promessa de demanda.

## RFID / Wokwi

Abra `wokwi/diagram.json` no Wokwi com ESP32 DevKit, RC522 e OLED SSD1306 128×64. O OLED usa I²C no endereço `0x3C`: `VCC → 3V3`, `GND → GND`, `SDA → GPIO 21` e `SCL → GPIO 17`. O sketch configura `Wire.begin(21, 17)` para manter o `GPIO 22` dedicado ao `RST` do RC522. A tela mostra o estado do leitor e a UID detectada; o Serial Monitor também imprime `RFID_UID=<UID>`. As bibliotecas estão listadas em `wokwi/libraries.txt`. Para facilitar a leitura, o mapa colorido do RC522 está em `wokwi/mapa-circuito.png` e o mapa do OLED está em `wokwi/mapa-oled.png`; os arquivos Mermaid correspondentes são editáveis. Consulte a [referência do OLED SSD1306 no Wokwi](https://docs.wokwi.com/parts/board-ssd1306) e o [guia Arduino da Adafruit](https://learn.adafruit.com/monochrome-oled-breakouts/arduino-library-and-examples). A UID ainda precisa ser copiada para o Nexo Estoque; o ESP32 simulado não envia movimentos ao FastAPI.

A tabela completa de pinos, explicação dos rótulos no ESP32 e instruções para abrir o circuito está em [`wokwi/mapa.md`](wokwi/mapa.md).

## Checagens

```bash
npm run check
npm run build
PYTHONPATH=backend .venv/bin/python -m compileall -q backend/app
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v
```

O login valida username e senha no backend; senhas são guardadas somente como hash scrypt com salt. `NEXO_SESSION_SECRET` assina cookies de sessão `HttpOnly` com expiração; no Preview HTTPS, o cookie usa `SameSite=None; Secure`, e o uso local em HTTP tem política separada. `NEXO_ADMIN_BOOTSTRAP_KEY` protege a criação do primeiro administrador e o endpoint é fechado quando já existe administrador ativo. As duas variáveis ficam no gerenciador de secrets do WebDev ou no `backend/.env` local, que é excluído do Git e do contexto Docker; exemplos contêm apenas placeholders. A API valida sessão, estado ativo e papel administrativo em cada rota protegida. Contas inativas não entram, o último administrador ativo não pode ser rebaixado/desativado, e a desativação lógica preserva a auditoria. Não há cadastro público, usuário compartilhado nem bypass de autenticação por modo de desenvolvimento.
