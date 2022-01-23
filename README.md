
# surfingcrypto

![img](docsrc/source/images/logo.png)

![img](https://img.shields.io/static/v1?label=python&message=3.7&color=blue&style=for-the-badge)

## Installation

1. With`conda` create new environtment for the project.

    ```shell
    conda env create -f environment.yml
    ```

2. Activate env to use repository.

    ```shell
    conda activate cryptoenv
    ```

3. Install with pip
   ```shell
   pip install .
   ```

## Configuration

In order to use the package, provide `surfingcrypto.config.config` class with the path to a folder containing a `config.json`. The json file must contain at least a dictionary of `coins`. It can also contain private keys for telegram and coinbase modules.

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


