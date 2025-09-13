# VeryEasyAI

Uma biblioteca de IA **extremamente simples** para chat, previsões, regressões, redes neurais e busca na internet.

Instalação (local/testing):
```
pip install -e .
```

Exemplo rápido:
```python
import veryeasyai as veai

bot = veai.ChatAI()
bot.treinar(["oi", "qual seu nome?"], ["Oi!", "Eu sou a VeryEasyAI!"])
print(bot.responder("oi"))
```
