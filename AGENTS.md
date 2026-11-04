# Pamuk VIP — Proje Kuralları

Bu depo, kaynak CloudStream depolarını aynalayan ve "Pamuk VIP" başlıkları için
`repo.json` / `plugins.json` üreten bir derleme projesidir. Üretici: `tools/pamuk.py`.

## Oturum başlangıcı (zorunlu)

Her yeni oturumda, kullanıcı bir şey istemeden önce:

1. `python tools/pamuk.py check` çalıştır.
2. Sonucu kullanıcıya kısa bir özet olarak bildir: hangi kaynakta kaç yeni eklenti,
   kaç sürüm güncellemesi, kaç kaldırılan, kaç hata var. Değişiklik yoksa "kaynaklarda
   güncelleme yok" de ve devam etme.
3. Değişiklik varsa `reports/last-check.md` içeriğini başlık başlık özetle ve
   **kullanıcıdan onay iste**.
4. Onay gelmeden `sync`, `build` veya `git push` **yapma**.

Onay geldikten sonra:

```bash
python tools/pamuk.py sync     # yeni/değişen .cs3 dosyalarını indirir
python tools/pamuk.py build    # repo.json + plugins.json + README üretir
python tools/pamuk.py verify   # link/hash doğrulaması (hata varsa dur)
git add -A && git commit -m "Kaynak güncellemeleri: ..."
```

`git push` yalnızca kullanıcı açıkça istediğinde yapılır.

## Üretilen dosyalar — elle düzenlemeyin

| Yol | Kaynağı |
| --- | --- |
| `builds/**/repo.json`, `builds/**/plugins.json` | `pamuk.py build` |
| `repo.json` (kök) | `pamuk.py build` |
| `README.md` | `pamuk.py build` |
| `docs/eklenti-envanteri.md`, `docs/kaynak-depolar.md` | `pamuk.py build` |
| `state/upstream.lock.json`, `state/build-summary.json` | `pamuk.py sync` |
| `plugins/**/*.cs3` | `pamuk.py sync` |
| `reports/last-check.md` | `pamuk.py check` |

Kalıcı değişiklikler şu dosyalarda yapılır:

- `config/sources.json` — kaynak depolar (yeni kaynak ekleme/çıkarma).
- `config/pamuk.json` — depo kimliği, başlıklar, sınıflandırma ve öncelik kuralları.
- `tools/pamuk.py` — üretici mantığı.

## Sınıflandırma kuralları

- `adult`: kaynak `adult` ise, `tvTypes` içinde `NSFW` varsa veya ad `adultKeywords`
  listesine uyuyorsa.
- `live` türü → `spor` (kaynak SPOR ya da ad `sportKeywords` ile eşleşiyorsa), aksi halde `tv`.
- Diğer eklentiler ad sinyaline (`groupKeywords`) göre tek ana başlığa atanır:
  `anime → belgesel → dizi → film → tv`.
- Türkçe dışı (`language != tr`) eklentiler ayrıca `dunya` başlığına eklenir.
- Elle atama için `config/pamuk.json` → `classification.pins` kullanılır
  (`{"EklentiAdi": "film"}` veya `{"EklentiAdi": ["film", "dizi"]}`).

## Teknik notlar

- Python 3.9+ ve yalnızca standart kütüphane kullanılır; ek bağımlılık yoktur.
- Tüm JSON/metin dosyaları UTF-8 ve LF satır sonuyla yazılır.
- `.cs3` dosya adları ASCII'ye çevrilir (Türkçe karakterler), URL'ler buna göre üretilir.
- Bir eklenti kaynaktan indirilemezse kayıt özgün (upstream) adresiyle yayınlanır;
  durum `sync` çıktısında ve `state/upstream.lock.json` içinde `mirrored: false` olarak görünür.
- Windows'ta komutlar `pamuk.cmd check|sync|build|verify|status` ile de çalıştırılabilir.
