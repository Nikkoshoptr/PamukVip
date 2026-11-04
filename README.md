# Pamuk VIP — CloudStream Eklenti Deposu

Pamuk VIP, **8 başlık** altında **285 eklenti** sunan bir CloudStream deposudur. Tüm eklenti dosyaları bu depoda aynalanır; kaynak depolar güncellendikçe buradaki sürümler de güncellenir.

- Depo: <https://github.com/Nikkoshoptr/PamukVip>
- Son derleme: **04.11.2026 18:29**

## Kurulum

1. CloudStream'i açın → **Ayarlar → Eklentiler → Depo ekle**.
2. Aşağıdaki ana linki yapıştırın ve kaydedin.
3. Depoya girip istediğiniz eklentileri indirin.

**Ana depo linki (Pamuk VIP — tüm başlıklar):**

```
https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/repo.json
```

## Başlık linkleri

Her başlık ayrı bir depo olarak da eklenebilir. Tek başlık eklerseniz yalnızca o gruptaki eklentiler listelenir.

| Başlık | Eklenti | Depo linki |
| --- | ---: | --- |
| **Pamuk VIP** (ana) | 285 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/repo.json |
| **Pamuk TV** | 25 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/tv/repo.json |
| **Pamuk Spor** | 35 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/spor/repo.json |
| **Pamuk Dizi** | 43 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/dizi/repo.json |
| **Pamuk Film** | 51 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/film/repo.json |
| **Pamuk Belgesel** | 3 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/belgesel/repo.json |
| **Pamuk Anime** | 12 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/anime/repo.json |
| **Pamuk Dünya** | 11 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/dunya/repo.json |
| **Pamuk Adult** (18+) | 117 | https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/adult/repo.json |

## Kaynak depolar

Bu depodaki eklentiler aşağıdaki kaynaklardan aynalanır. Kaynaklar güncellendiğinde `check → sync → build` akışıyla buraya aktarılır.

| Kaynak | Depo | Aynalanan |
| --- | --- | ---: |
| PARS | <https://github.com/punistek/PARS-CloudStream-Builds> | 79/79 |
| SPOR | <https://github.com/Wiojelt/WioSpor> | 29/29 |
| TURK | <https://github.com/Wiojelt/WioSinema> | 37/37 |
| MRC | <https://github.com/lepotane/MRC-builds> | 73/73 |
| KARAYEL | <https://github.com/karayel90/cloudplug> | 1/1 |
| XXX +18 | <https://github.com/Kraptor123/Cs-GizliKeyif> | 110/110 |

## Güncelleme akışı

```bash
python tools/pamuk.py check    # kaynaklarda ne değişti? (rapor: reports/last-check.md)
python tools/pamuk.py sync     # onay sonrası: yeni/değişen eklentileri indir
python tools/pamuk.py build    # repo.json + plugins.json + bu README'yi üret
python tools/pamuk.py verify   # linkleri ve dosya hash'lerini doğrula
```

Windows'ta kısayol: `pamuk.cmd check`, `pamuk.cmd sync`, `pamuk.cmd build`, `pamuk.cmd verify`.

## Klasör yapısı

```
config/     kaynak depolar ve başlık tanımları
plugins/    aynalanan .cs3 eklenti dosyaları (kaynak başına klasör)
upstream/   kaynak repo.json / plugins.json kopyaları
builds/     CloudStream'in okuduğu repo.json + plugins.json (başlık başına)
state/      kaynak sürüm kilidi (upstream.lock.json) ve derleme özeti
reports/    son güncelleme kontrolü raporu
tools/      pamuk.py üreteci
```

## Notlar

- Her eklenti, adı ve ana türüne göre tek bir başlıkta listelenir; Türkçe dışı eklentiler ayrıca **Pamuk Dünya** başlığında görünür.
- Aynı eklenti birden fazla kaynakta varsa en yüksek sürümlü kayıt yayınlanır (kaynak önceliği: mrc → turk → pars → spor → karayel → adult).
- Kaynaktan indirilemeyen eklentiler, çalışmaya devam etmesi için özgün adresiyle yayınlanır.
- Pamuk Adult başlığı 18+ içerik barındırır; CloudStream'de yetişkin içerik ayarı kapalıysa görünmez.

## Yasal uyarı

Bu depo yalnızca açık kaynak CloudStream eklentilerini bir araya getirir ve hiçbir içerik barındırmaz. Eklentiler üçüncü taraf sitelere bağlanır; içeriklerin yasallığı ve kullanım sorumluluğu kullanıcıya aittir. 18+ başlığındaki içerikler yalnızca reşit kullanıcılar içindir.
