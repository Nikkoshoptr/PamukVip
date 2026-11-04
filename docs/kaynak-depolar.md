# Kaynak Depolar

Pamuk VIP deposu aşağıdaki kaynaklardan beslenir. Bu dosya `config/sources.json` temel alınarak üretilir.

| Kaynak | Depo sayfası | Manifest (repo.json) | Eklenti listesi | Eklenti |
| --- | --- | --- | --- | ---: |
| PARS | <https://github.com/punistek/PARS-CloudStream-Builds> | <https://raw.githubusercontent.com/punistek/PARS-CloudStream-Builds/refs/heads/builds/repo.json> | <https://raw.githubusercontent.com/punistek/PARS-CloudStream-Builds/refs/heads/builds/plugins.json> | 79 |
| SPOR | <https://github.com/Wiojelt/WioSpor> | <https://raw.githubusercontent.com/Wiojelt/WioSpor/main/repo.json> | <https://raw.githubusercontent.com/Wiojelt/WioSpor/builds/plugins.json> | 29 |
| TURK | <https://github.com/Wiojelt/WioSinema> | <https://raw.githubusercontent.com/Wiojelt/WioSinema/main/repo.json> | <https://raw.githubusercontent.com/Wiojelt/WioSinema/main/plugins.json> | 37 |
| MRC | <https://github.com/lepotane/MRC-builds> | <https://raw.githubusercontent.com/lepotane/MRC-builds/builds/repo.json> | <https://raw.githubusercontent.com/lepotane/MRC-builds/builds/plugins.json> | 73 |
| KARAYEL | <https://github.com/karayel90/cloudplug> | <https://raw.githubusercontent.com/karayel90/cloudplug/refs/heads/main/repo.json> | <https://raw.githubusercontent.com/karayel90/cloudplug/refs/heads/builds/plugins.json> | 1 |
| XXX +18 | <https://github.com/Kraptor123/Cs-GizliKeyif> | — | <https://raw.githubusercontent.com/Kraptor123/Cs-GizliKeyif/builds/plugins.json> | 110 |

## Notlar

- **PARS**: Türkçe dizi/film/canlı TV ağırlıklı; içindeki yetişkin eklentiler Pamuk Adult başlığına yönlendirilir.
- **SPOR**: Canlı spor ve IPTV kanalları.
- **TURK**: TMDB destekli birleşik Türkçe sinema ve dizi eklentileri.
- **MRC**: Türkçe dizi, film, anime ve canlı kanallar.
- **KARAYEL**: Tabii başta olmak üzere canlı yayın eklentileri.
- **XXX +18**: Yalnızca yetişkin (18+) içerik. Pamuk Adult başlığı altında yayınlanır.

Kaynak JSON'larının son kopyaları `upstream/<kaynak>/` altında, eklenti dosyaları `plugins/<kaynak>/` altında tutulur.
