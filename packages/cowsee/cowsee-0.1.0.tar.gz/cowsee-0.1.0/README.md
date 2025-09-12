# cowsee
"A picture is worth a thousand words." -the cow

Visualize geometry data in the command line, along with the famous [talking cow](https://github.com/cowsay-org/cowsay).

```console
$ cowsee hello_world.shp
╔════════════════════════════════════════════════════════════════════════════╗                    
║                                                                            ║
║                      /─\   /─┬─╴                                           ║
║              /─┬┬┬┬┬─┴─┴─┬─┴╴\──┬─╴    ╶──╴  ╶──┬┬╴╶─╴/────\   /┬┬╴        ║
║   ╷ /────┬───┴┬┼┼┼┼┼┬─┬─\\┬╴   /┴╴     /┬┬┬─\╷/┬┴┴┬┬┬─/  ╶─┴───┴┴┴─────\   ║
║   \─┼╴ ╷╷|    \┴┴┴┼┴┴┬┴┬┴╴\┬┬──/╶─╴  /┬┼┼┤├─┴┴┴/  \┴/              /┬╴//   ║
║    ╶┼──┴┴┴─┬\     \─\├╴\─\ \/      /\\┼┼┴┼┴\    /──┬\          /┬──┼┼─/    ║
║   ╶─/      \┼───────┼/ /┬┼\       ╶┴┼─┼┼┬┼┬┼\ /┬/  ╵\┬┬─────┬─┬┼┼╴╷\/      ║
║             |       \─┬┴┴/╵        /┴┬┼┼┼┼┼┴┴┬┼┼─┬┬┬─/\─────┼┬┼/├╴╵        ║
║             \─\      //        ╶╴  ├┬┴┼┼┴┼┴┬┬┴┼┴┬┴┼┼\      ╶┤\┼─/          ║
║              ╶┴┬┬─┬──┼\          ╶┬┼┤ ├┼─┼─┼┼─┼┬┼┬┼/\─┬┬\   |╶/            ║
║      ╶╴        \┴┬┴┬─┴┼┬\        //├┴┬┴┼─┼─┴┼┬┼┼/╵\\ /┴┼┼┬──┤              ║
║                  \─┴\ ├┼┼\       \┬┼┬┼─┼╴| /┴┼┼/   |///┴┼┼╴ ├\             ║
║                     \┬┴┼┼┼┬\      \┴┴┴┬┼┬┴┬┼─┼┤    ├/ \┬┼┼\/┴┤    ╶╴ ╶╴    ║
║    ╷                 ├─┼/\┴┴─\        \┼┤ ├┴┬┴/    ╵   \┼┼┴┼┬┼┬┬┬\╷   ╶╴   ║
║    ╵     ╶╴          |╶┼\    ├╴        ├┴\├\|╶╴         \┴─┴┼┴/\┼┴/╶\╷     ║
║   \╶╴  ╶╴            \─┤\\   |         ├┬┼┼┼┤/\             ├───┴\  ╵╵ ╷   ║
║   ╵      ╶╴            ├─┼\/─/         |├┼┴┼/||           /┬/    \\ ╶─╴╵   ║
║                       /┤ ├┼/           \┼/// \/           \┤ /\   |        ║
║                       ||/┴/             \─/                \─/\─┬─/   /\   ║
║                       ├┼/                                       \╴   /┴/   ║
║                       ├┼╴    ╷                                       ╵     ║
║                       \┴╴ ╷  \╴                                            ║
║                        /─┬/                  /───\  /─────────────\        ║
║          /─────────────/╶┤      /────────────/   \──/             \─┬─╴    ║   ^__^
║   /──────/               \──────/                                   \──\   ║   (oo)\_______
║   ├┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┬┤   ║   (__)\       )\/\
║                                                                            ║       ||----w |
╚════════════════════════════════════════════════════════════════════════════╝       ||     ||
```

> [!NOTE]  
> `cowsee` requires a monospaced font to be properly displayed without looking real funky.

## Setup

Package and environment management is handled by [uv](https://docs.astral.sh/uv/guides/install-python/). 

```console
$ uv sync
```

```console
$ source .venv/bin/activate   # Linux/macOS
$ .venv\Scripts\activate      # Windows
```

## Run

To run, it is as simple as:

```console
$ cowsee <filepath/url>
```

Anything that can be read by `geopandas.read_file()` can be handled by `cowsee`. 
This includes links! Try saying "hello world" yourself:

```console
$ cowsee https://international.ipums.org/international/resources/gis/IPUMSI_world_release2024.zip
```

Supports Polygon, LineString, and Point data.

To output a larger or smaller image, the maximum width can be defined using the `--width` or `-w` flag.

Complex Line and Polygon geometries can sometimes visually benefit from some simplification before drawing. 
This can be achieved by adding the `--simplify-ratio` or `-s` flag. 

Finally, if you don't want to see the cow (said no one, ever) you can pass the `--no-cow` flag.

## Looking Ahead

- Testing coverage
- Raster data support
