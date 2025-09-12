<div align="center">
  <a href="https://github.com/ventuero/brostel">
    <img src="https://raw.githubusercontent.com/ventuero/brostel/master/assets/logo.png" alt="Brostel" width="160" height="160">
  </a>

  <h1 align="center">Brostel</h1>

  <p align="center">
    Telegram formatting tool for <a href='https://github.com/timoniq/telegrinder'>telegrinder</a>
  </p>
</div>

## 🌍 Documentation

- **🇷🇺 Русский**: [docs/ru/README.md](docs/ru/README.md)
- **🇺🇸 English**: [docs/en/README.md](docs/en/README.md)

## 🚀 Quick Start

```bash
pip install brostel
```

```python
from brostel import brostel
from telegrinder import API, Message, Telegrinder, Token

bot = Telegrinder(API(Token.from_env()))

@bot.on.message()
async def handler(msg: Message):
    await (
        brostel(msg)
        .tags(user=msg.from_user.first_name)
        .reply(msg)
    )
```

## ✨ Key Features

- 📐 **Solves entity-position mismatch** - correct entities after tag replacement
- 🛡️ **Controlled HTML processing** - Sulguk ensures safe tag handling
- 🏷️ **Dynamic tags** - `%placeholder%` replacement with proper entities
- 🔘 **Auto inline buttons** - create keyboards from `[Text](URL)` syntax
- ⚙️ **Global configuration** - set once, use everywhere
- 🎯 **Method chaining** - `brostel(text).tags(user="John").reply(msg)`

## 📄 License

This project is licensed under the [MIT License](https://github.com/ventuero/brostel/blob/master/LICENSE).\
Copyright © 2025 [ventuero](https://github.com/ventuero)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

- GitHub Issues: [Create an issue](https://github.com/ventuero/brostel/issues)
- Telegram: [@ventuero](https://t.me/ventuero)