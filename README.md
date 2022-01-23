
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

3. Run setup in editable mode to allow importing from anywhere within the environment and set it in editable `-e` mode.
   ```shell
   pip install -e .
   ```

## Configuration

To use the package a file `config.json` containing configuration is required. It contains also private keys for telegram and coinbase modules.

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

Documentations is temporarily  hosted [here](http://crypto-documentation-website.s3-website.eu-central-1.amazonaws.com) on an AWS S3 bucket with public access.

### Build the docs and share docs 

Documentation is obtained by executing following script. Allows to share online if `AWS CLI` credentials are installed on the machine.

`sphinx` in required and `./tools/build-docs.sh` must be executable.

```shell
./tools/build-docs.sh
```

## Branching and versioning logic 

*in the future will be switched to a more CI-favourable approach*

The repository is *kinda* based onto a gitflow approach. There is a `main` and `develop` branch. 

- `main`  is the relase version, tagged with version number. It is the version that is installed on remote server. It can only receive merges from `developement`.
- `develop` is the *release* and *developement* version alltogheter. It is the last step before the release (a.k.a. installation on server). Can be also be independently modified.

In addition:
- `hotfix/` branches are quick fixes of main branches. Will be merged only into `main` or `develop`
- `feature/` branches are the actual developement branches, where new features are implemented.

The branching and versioning logic can be represented with the following diagram:

```
Tags               v0.2        v0.3         v0.4

main             ---o-----------o-----------o
                     \         /           /
hotfix                o---o---o           /
                               \         /
develop          ---o-----o-----o---o---o---o-->
                     \         /     \
feature1              o---o---o       \
feature2                               o---o-->
etc...
```
