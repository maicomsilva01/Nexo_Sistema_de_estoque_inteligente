# Arquitetura — Nexo Estoque

## Componentes

```text
Navegador / Manus Preview
        │ mesmo origin: React Router + Vite (dev :3000)
        ├── /api/* ── proxy no desenvolvimento ── FastAPI (dev :8000)
        └── /_app/health
                                  │
                         SQLAlchemy + DATABASE_URL
                                  │
                    MySQL gerenciado do projeto
```

No container publicado, o FastAPI atende API, health check e os arquivos de `frontend/dist/` em um processo/porta. O build do Vite é compilado na etapa Node do `Dockerfile`; o container final é Python. O Preview público é HTTPS, mesmo quando o servidor local recebe HTTP por proxy; URLs do navegador são relativas e a aplicação não deriva origem pública do host interno.

## Fluxos

- **Identidade:** a pessoa informa username individual e senha. O backend normaliza o username e valida o hash scrypt da senha; respostas de credencial incorreta não distinguem nome inexistente de senha errada. Login exige o marcador de schema v4 e falha com HTTP 503 antes dele. O primeiro administrador só é criado pelo endpoint de bootstrap protegido por `NEXO_ADMIN_BOOTSTRAP_KEY`; a disponibilidade termina quando há admin ativo. Não há cadastro público, convite nem conta compartilhada.
- **Sessão:** a API assina JWT HS256 com `NEXO_SESSION_SECRET`, validade de 12 horas e subject `open_id`; cada requisição valida o marcador v4 e resolve a conta ativa no banco. O cookie da aplicação é `nexo_user_session`, `HttpOnly`, `SameSite=None; Secure` no Preview HTTPS e usa configuração separada no HTTP local. Mutações exigem a marca de requisição da aplicação. Nenhum segredo ou senha é embutido no bundle.
- **Permissões:** somente admin ativo pode listar, criar, editar, redefinir senha, ativar ou desativar contas. Todas as alterações exigem v4, usam lock transacional comum, revalidam o ator e protegem o último admin ativo. O frontend também oculta e protege a navegação administrativa, sem substituir a autorização backend.
- **Saldo:** produto tem `estoque_inicial`; cada movimento imutável guarda tipo, quantidade, autor, motivo, origem e data. Entrada soma, saída subtrai, ajuste soma quantidade assinada. A API verifica que o saldo após a operação não fica negativo.
- **Alertas:** saldo menor ou igual ao mínimo vira item de atenção; saldo zero/negativo tem severidade de ruptura. Reposição sugerida é `máximo(2 × mínimo − saldo, 0)`, uma sugestão operacional, não uma ordem de compra.
- **Previsão:** saídas diárias dos últimos 30 dias alimentam ajuste linear leve. Históricos curtos recebem média simples explicitamente marcada; ausência de histórico não vira previsão artificial.
- **RFID:** `rfid_service` normaliza UID, encontra o produto e entrega leitura ao mesmo criador de movimentação. O Wokwi imprime UID serial; o operador transfere a UID para o formulário de demonstração.

## Limites

A versão inicial não tem ERP, depósitos múltiplos, lotes/validade, compra automática, sincronização de leitor físico ou papéis empresariais granulares. Cada conta guarda um username único; e-mail é opcional, não autentica nem dispara mensagens. Movimentações continuam associadas ao nome da pessoa autenticada. Custos/valor e previsões dependem dos dados preenchidos.
