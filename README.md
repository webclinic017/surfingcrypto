
# surfingcrypto

![img](docsrc/source/images/logo.png)

![Python](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20-blue)
![GitHub Workflow Status](https://img.shields.io/github/workflow/status/giocaizzi/surfingcrypto/ci)
![Codecov](https://img.shields.io/codecov/c/gh/giocaizzi/surfingcrypto)

## Installation

1. Clone repo
    ```shell
    git clone git@github.com:giocaizzi/surfingcrypto.git
    ```
2. Install requirements.

    ```shell
    pip install -r requirements.txt
    ```

3. Install package with `pip`
   ```shell
   pip install .
   ```

## Configuration

In order to use the package, provide `surfingcrypto.Config` class with the path to a folder containing a `config.json`. The json file must contain at least a dictionary of `coins`. It can also contain private keys for `telegram` and `coinbase` modules.

```
{
    "coins":
    {
        "BTC":"",
        "ETH":"",
        "MATIC":"",
        "ADA":"",
        "SOL":""
    },
    "telegram":
    {
        "token":"XXXXXXXXXX"
    },
    "coinbase":
    {
        "key":"XXXXXXXXXX",
        "scrt":"XXXXXXXXXX"
    }
    
}
```

## Documentation

### Read the docs

Documentations can be found [here](https://giocaizzi.github.io/surfingcrypto/)


