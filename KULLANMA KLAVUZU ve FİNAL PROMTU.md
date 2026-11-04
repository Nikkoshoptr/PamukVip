# KULLANMA KLAVUZU ve FİNAL PROMTU

> Bu dosya projenin **güncel** durumunu anlatır: ne olduğu, ne yapabildiği, nasıl kullanıldığı,
> son yapılan değişiklikler ve projeyi sıfırdan birebir yeniden üretebilecek final promptu.
> Geçmiş/revizyon arşivi tutulmaz; her güncellemede yalnızca güncel bilgiler yazılır.

---

## 1. Proje kimliği

| Alan | Değer |
| --- | --- |
| **Ad** | Pamuk VIP — CloudStream Eklenti Deposu |
| **Konum** | `D:\AI - PROJELERIM\PAMUK VIP - CLOUDSTREAM` |
| **GitHub** | <https://github.com/Nikkoshoptr/PamukVip> (dal: `main`, herkese açık) |
| **Tür** | Veri aynalama + JSON üretim projesi (uygulama değil, derleme hattı) |
| **Dil / bağımlılık** | Python 3.9+ (yalnızca standart kütüphane), Git |
| **Giriş noktası** | `tools/pamuk.py` (Windows kısayolu: `pamuk.cmd`) |
| **Ana çıktı** | Kök `repo.json` + `builds/<başlık>/repo.json` ve `plugins.json` |

## 2. Kullanım amacı

Altı ayrı Türkçe CloudStream eklenti deposunu **tek çatı altında** toplamak: eklentileri kendi
GitHub deposunda aynalamak, kaynak depolar güncellendiğinde değişiklikleri tespit etmek,
kullanıcı onayıyla aktarmak ve içerikleri **başlık başlık** (Canlı, Spor, Dizi, Film, Belgesel,
Anime, Dünya, Adult) ayrı linklerle sunmak.

## 3. Kullanım alanları

- CloudStream uygulamasına depo linki eklemek (tek başlık veya tüm başlıklar).
- Kaynak depoların sürüm takibini yapmak (hangi eklenti hangi sürüme çıktı, ne eklendi, ne kaldırıldı).
- Eklenti envanteri / içerik kataloğu çıkarmak (`docs/eklenti-envanteri.md`).
- Yeni kaynak depo ekleyerek kapsamı büyütmek.
- Kaynak deposu kapanan/bozulan eklentileri kendi aynasından yayınlamaya devam etmek.

## 4. Yetenek listesi

- **Çoklu kaynak okuma:** her kaynak için `repo.json` (manifest) → `pluginLists` → `plugins.json`
  zincirini izler; manifest yoksa doğrudan liste adresini kullanır.
- **Aynalama:** 329 `.cs3` dosyasını kaynak başına klasöre indirir; ASCII dosya adı üretir,
  Türkçe karakterli URL'leri yüzde kodlar.
- **Bütünlük:** her dosyanın `sha256-<hex>` özetini ve boyutunu `plugins.json` içine yazar;
  `verify` bunları yeniden hesaplayıp karşılaştırır.
- **Değişiklik tespiti:** yeni / kaldırılan / sürümü artan / adresi veya hash'i değişen eklentileri
  kaynak bazında raporlar (`reports/last-check.md`).
- **Sürüm yönetimi:** kaynak sürümü artmazsa ama dosya içeriği değişirse yayın sürümünü +1 artırır;
  böylece CloudStream güncellemeyi görür.
- **Tekilleştirme:** aynı `internalName` birden fazla kaynakta varsa en yüksek sürümlü kaydı seçer,
  eşitlikte `config/pamuk.json → dedupe.sourcePriority` sırasını uygular.
- **Sınıflandırma:** eklentiyi ad sinyali + `tvTypes` + dil bilgisine göre tek ana başlığa atar;
  `classification.pins` ile elle atama yapılabilir.
- **Kademeli bozulma:** indirilemeyen eklenti listeden düşmez, özgün (upstream) adresiyle yayınlanır
  ve `mirrored: false` olarak işaretlenir.
- **Üretim:** 9 adet `plugins.json` + 9 adet `repo.json` + kök `repo.json` + `README.md` +
  `docs/eklenti-envanteri.md` + `docs/kaynak-depolar.md`.
- **Doğrulama:** `verify` tüm listelerde tekrar eden `internalName`, eksik dosya, boyut/hash
  uyuşmazlığı ve geçersiz URL arar; hata varsa çıkış kodu 1'dir.
- **Durum özeti:** `status` kaynak/başlık bazında sayıları ve yayın linklerini listeler.

## 5. Kullanım kılavuzu

### 5.1. Son kullanıcı (CloudStream)

1. CloudStream → **Ayarlar → Eklentiler → Depo ekle**.
2. Ana linki yapıştır: `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/repo.json`
   (yalnızca tek başlık isteniyorsa aşağıdaki tablodan o başlığın linki eklenir).
3. Depoyu aç, istediğin eklentiyi indir. 18+ içerik için uygulamada yetişkin içerik ayarı açık olmalı.

### 5.2. Yayın linkleri (güncel)

| Başlık | Eklenti | Depo linki |
| --- | ---: | --- |
| **Pamuk VIP** (ana) | 285 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/repo.json` |
| Pamuk Canlı | 25 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/canli/repo.json` |
| Pamuk Spor | 35 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/spor/repo.json` |
| Pamuk Dizi | 43 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/dizi/repo.json` |
| Pamuk Film | 51 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/film/repo.json` |
| Pamuk Belgesel | 3 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/belgesel/repo.json` |
| Pamuk Anime | 12 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/anime/repo.json` |
| Pamuk Dünya | 11 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/dunya/repo.json` |
| Pamuk Adult (18+) | 117 | `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/builds/adult/repo.json` |

### 5.3. Bakım / güncelleme akışı (zorunlu sıra)

```bash
python tools/pamuk.py check     # 1) kaynaklarda ne değişti? (indirme yapmaz, rapor yazar)
#    -> raporu kullanıcıya özetle, ONAY AL
python tools/pamuk.py sync      # 2) yeni/değişen .cs3 dosyalarını indir, lock + upstream kopyalarını güncelle
python tools/pamuk.py build     # 3) repo.json / plugins.json / README / envanter üret
python tools/pamuk.py verify    # 4) link + boyut + hash doğrula (hata varsa dur)
git add -A && git commit -m "Kaynak güncellemeleri: ..."
```

- Windows kısayolları: `pamuk.cmd check|sync|build|verify|status` (dosya CRLF ile yazılmalıdır).
- `sync --force` tüm dosyaları yeniden indirir.
- GitHub sahip/repo/branch değişecekse: `python tools/pamuk.py set-repo --owner X --slug Y --branch main`
  (config'i güncelleyip otomatik yeniden derler).
- `git push` yalnızca kullanıcı açıkça istediğinde yapılır.
- İlk kurulumdan sonra `check` "kaynaklarda güncelleme yok" derse yapılacak iş yoktur.

### 5.4. Kaynak deposu ekleme

`config/sources.json` → `sources` dizisine yeni kayıt ekle:

```json
{
  "id": "kisa-kimlik",
  "label": "GÖRÜNEN AD",
  "title": "Depo başlığı",
  "repoUrl": "https://github.com/kullanici/depo",
  "manifestUrl": "https://raw.githubusercontent.com/.../repo.json",
  "pluginsJson": "https://raw.githubusercontent.com/.../plugins.json",
  "givenUrls": ["..."],
  "note": "kısa açıklama",
  "adult": false
}
```

Sonra `check` → onay → `sync` → `build` → `verify`.

### 5.5. Sınıflandırmayı düzeltme

`config/pamuk.json` → `classification.pins`:

```json
{ "EklentiAdi": "film", "BaskaEklenti": ["dizi", "dunya"] }
```

`"skip"` verilirse eklenti hiçbir başlığa girmez. Değişiklikten sonra `pamuk.cmd build` yeterlidir.

## 6. Proje yapısı (güncel)

```
config/sources.json              kaynak depolar (6 kayıt)
config/pamuk.json                depo kimliği, başlıklar, sınıflandırma/öncelik kuralları
tools/pamuk.py                   üretici (check/sync/build/verify/status/set-repo/all)
pamuk.cmd                        Windows kısayolu (CRLF)
plugins/<kaynak>/*.cs3           329 aynalanan eklenti dosyası (~25 MB)
upstream/<kaynak>/               repo.json + plugins.json kopyası + SOURCE.md
builds/<başlık>/                 repo.json + plugins.json (9 liste: 8 başlık + pamuk-vip)
builds/pamuk-vip/                ana (tüm başlıklar) liste
repo.json                        kök ana depo dosyası (Pamuk VIP)
state/upstream.lock.json         kaynak sürüm/hash kilidi (329 kayıt)
state/build-summary.json         son derleme özeti
docs/eklenti-envanteri.md        başlık bazlı eklenti tablosu (üretilir)
docs/kaynak-depolar.md           kaynak adres tablosu (üretilir)
docs/kaynak-listeleri/           eski PARS envanteri (arşiv)
reports/last-check.md            son kontrol raporu (git'e girmez)
README.md                        kullanıcıya dönük tanıtım + link tablosu (üretilir)
AGENTS.md                        oturum kuralları (check zorunluluğu)
.gitattributes                   * text=auto eol=lf, *.cs3 binary, *.cmd eol=crlf
```

**Elle düzenlenmez:** `builds/**`, kök `repo.json`, `README.md`, `docs/eklenti-envanteri.md`,
`docs/kaynak-depolar.md`, `plugins/**`, `state/upstream.lock.json`, `state/build-summary.json`,
`reports/**` — hepsi üretilir. Kalıcı değişiklik `config/` ve `tools/` altında yapılır.

## 7. Teknik sözleşmeler (bozulmamalı)

- `repo.json`: `{name, description, manifestVersion: 1, pluginLists: [<mutlak url>], lastUpdated, pluginCount}`.
- `plugins.json` kaydı: `name, internalName, version, url, status: 1, apiVersion, language, tvTypes, authors, description, repositoryUrl, fileSize, fileHash ("sha256-<hex>")`, varsa `iconUrl`.
- Eklenti URL'leri: `https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main/plugins/<kaynak>/<Dosya>.cs3`.
- `internalName` bir liste içinde **tek** olmalı; `status` her zaman `1` (etkin) yayınlanır.
- Dosya adları ASCII'ye çevrilir (`ç→c, ğ→g, ı→i, İ→I, ö→o, ş→s, ü→u`), çakışma olursa `-2` eki.
- Tüm dosyalar UTF-8 + LF (batch dosyası hariç CRLF); JSON'lar 2 boşluk girintili ve `ensure_ascii=False`.
- `.cs3` dosyaları git'te ikili kabul edilir; satır sonu dönüşümü hash'i bozar.

## 8. Güncel durum

| Ölçüt | Değer |
| --- | --- |
| Kaynak depo | 6 |
| Kaynak eklenti kaydı | 329 |
| Benzersiz eklenti (ana liste) | 285 |
| Başlık listelerindeki toplam kayıt | 582 |
| Aynalanan dosya | 329 / 329 (upstream'e düşen yok) |
| Üretilen liste dosyası | 9 |
| Depo boyutu (git) | ~25 MB |
| Son kontrol sonucu | Kaynaklarda güncelleme yok |

Başlık dağılımı: Canlı 25, Spor 35, Dizi 43, Film 51, Belgesel 3, Anime 12, Dünya 11, Adult 117.
Belgesel sayısı düşüktür çünkü kaynaklarda belgesel türünde yalnızca 3 eklenti var.

## 9. Son yapılan değişiklikler (güncel)

- Depo sıfırdan oluşturuldu: 6 kaynaktan 329 eklenti aynalandı, 285 benzersiz kayıt üretildi.
- Başlık bazlı 9 liste (8 başlık + ana liste) ve kök `repo.json` üretildi, GitHub'a gönderildi.
- Sınıflandırma tek ana başlığa indirildi (upstream'in geniş `tvTypes` alanı yüzünden listeler
  birbirinin kopyası oluyordu); Türkçe dışı eklentiler ek olarak `dunya` başlığına alındı.
- `İnfluencerChicks` gibi Türkçe karakterli adresler için URL yüzde kodlaması eklendi.
- "Pamuk TV" başlığı **Pamuk Canlı** olarak yeniden adlandırıldı; link yolu `builds/tv/` → `builds/canli/`
  olarak değişti (grup kimliği de `canli`), eski `builds/tv/` klasörü kaldırıldı.
- `pamuk.cmd` CRLF satır sonuna alındı ve `.gitattributes` ile sabitlendi (batch dosyası LF ile bozuluyordu).
- `reports/` git takibinden çıkarıldı (her kontrolde değişen üretilmiş rapor).
- `KULLANMA KLAVUZU ve FİNAL PROMTU.md` eklendi; `AGENTS.md`'ye bu dosyanın her revizyonda
  güncellenmesi kuralı işlendi.
- Doğrulama: canlı linkler HTTP 200, indirilen `.cs3` hash'i manifestle birebir aynı, `verify` temiz.

## 10. Bilinen sınırlar

- Kaynak depolar üçüncü taraftır; eklenti kodu bu projede geliştirilmez, yalnızca aynalanır.
- `status` alanı tüm kayıtlarda `1` yayınlanır (kaynağın "çalışmıyor" işareti korunmaz).
- `.cs3` dosyaları Git LFS kullanmaz; depo boyutu kaynaklarla birlikte büyür.
- GitHub Actions ile otomatik zamanlanmış senkron **yoktur**; kontrol oturum açılışında `check` ile yapılır.
- CloudStream uygulaması bu makinede kurulu olmadığı için listeler uygulama içinde denenmemiştir;
  doğrulama JSON şeması, canlı HTTP erişimi ve dosya hash'leri üzerinden yapılır.

---

## 11. FİNAL PROMPT — projeyi sıfırdan aynı hale getirme

> Aşağıdaki metni boş bir klasörde yeni bir oturuma vererek bu projeyi baştan üretebilirsin.

```text
"D:\AI - PROJELERIM\PAMUK VIP - CLOUDSTREAM" klasöründe, GitHub'da Nikkoshoptr/PamukVip
(main dalı) deposuna gönderilecek bir CloudStream eklenti aynalama projesi kur.

AMAÇ
Altı kaynak CloudStream deposundaki tüm eklentileri kendi depomda aynala, kaynaklar
güncellendiğinde değişiklikleri kullanıcıya raporla, onay alınca aktar ve eklentileri
başlık başlık ayrı linklerle sun. Ana linkin adı "Pamuk VIP" olsun.

KAYNAKLAR (config/sources.json içine id/label/title/repoUrl/manifestUrl/pluginsJson/note/adult
alanlarıyla kaydet; manifestUrl ile pluginsJson ikisini de tut, givenUrls ile verilen adresleri koru)
- pars    | PARS    | https://github.com/punistek/PARS-CloudStream-Builds
  manifest: https://raw.githubusercontent.com/punistek/PARS-CloudStream-Builds/refs/heads/builds/repo.json
  liste:    https://raw.githubusercontent.com/punistek/PARS-CloudStream-Builds/refs/heads/builds/plugins.json
- spor    | SPOR    | https://github.com/Wiojelt/WioSpor
  manifest: https://raw.githubusercontent.com/Wiojelt/WioSpor/main/repo.json
  liste:    https://raw.githubusercontent.com/Wiojelt/WioSpor/builds/plugins.json
- turk    | TURK    | https://github.com/Wiojelt/WioSinema
  manifest: https://raw.githubusercontent.com/Wiojelt/WioSinema/main/repo.json
  liste:    https://raw.githubusercontent.com/Wiojelt/WioSinema/main/plugins.json
- mrc     | MRC     | https://github.com/lepotane/MRC-builds
  manifest: https://raw.githubusercontent.com/lepotane/MRC-builds/builds/repo.json
  liste:    https://raw.githubusercontent.com/lepotane/MRC-builds/builds/plugins.json
- karayel | KARAYEL | https://github.com/karayel90/cloudplug
  manifest: https://raw.githubusercontent.com/karayel90/cloudplug/refs/heads/main/repo.json
  liste:    https://raw.githubusercontent.com/karayel90/cloudplug/refs/heads/builds/plugins.json
- adult   | XXX +18 | https://github.com/Kraptor123/Cs-GizliKeyif
  manifest: yok
  liste:    https://raw.githubusercontent.com/Kraptor123/Cs-GizliKeyif/builds/plugins.json
  adult: true

BAŞLIKLAR (config/pamuk.json -> groups; sıra önemli)
canli=Pamuk Canlı, spor=Pamuk Spor, dizi=Pamuk Dizi, film=Pamuk Film, belgesel=Pamuk Belgesel,
anime=Pamuk Anime, dunya=Pamuk Dunya, adult=Pamuk Adult (18+).
Ana/agregate liste kimliği: pamuk-vip, adı "Pamuk VIP".
Depo kimliği: owner=Nikkoshoptr, slug=PamukVip, branch=main,
taban = https://raw.githubusercontent.com/Nikkoshoptr/PamukVip/main

ÜRETİCİ: tools/pamuk.py (Python 3.9+, yalnızca standart kütüphane). Alt komutlar:
- check : her kaynağın manifestini ve listelerini okur, state/upstream.lock.json ile
          karşılaştırır; yeni/kaldırılan/sürüm artışı/adres-hash değişimi çıkarır;
          kaynak bazında özet + ayrıntıyı reports/last-check.md dosyasına yazar. İndirme yapmaz.
- sync  : yeni veya meta verisi değişen .cs3 dosyalarını plugins/<kaynak>/ altına indirir
          (değişmeyeni yeniden kullanır), sha256 hesaplar, upstream JSON kopyalarını
          upstream/<kaynak>/ altına yazar, lock'u günceller. URL'leri yüzde kodlar;
          indirilemeyen eklenti mirrored:false olarak işaretlenir (upstream adresiyle yayınlanır).
- build : lock'tan yayın kayıtlarını üretir, sınıflandırır, tekilleştirir; her başlık için
          builds/<id>/plugins.json + repo.json, ayrıca builds/pamuk-vip/ ve kök repo.json,
          README.md, docs/eklenti-envanteri.md, docs/kaynak-depolar.md yazar.
- verify: her listede tekrar eden internalName, eksik dosya, boyut/hash uyuşmazlığı ve
          geçersiz URL arar; sorun varsa çıkış kodu 1.
- status, set-repo --owner/--slug/--branch, all (sync+build+verify).

KURALLAR
- plugins.json kaydı: name, internalName, version, url, status=1, apiVersion, language,
  tvTypes, authors, description, repositoryUrl (bizim repo sayfası), fileSize,
  fileHash "sha256-<hex>", varsa iconUrl.
- repo.json: name, description, manifestVersion=1, pluginLists=[mutlak url], lastUpdated, pluginCount.
- Sınıflandırma: kaynak adult ise / tvTypes içinde NSFW varsa / ad adultKeywords'e uyuyorsa => adult.
  live türü => kaynak "spor" ise ya da ad sportKeywords'e uyuyorsa spor, değilse canli.
  Diğerleri: önce ad sinyali (groupKeywords: anime -> belgesel -> dizi -> film -> canli),
  sonra tür sinyali; her eklenti TEK ana başlığa atanır. language != tr ise ayrıca dunya.
  Elle atama: classification.pins {"Ad": "film"} veya {"Ad": ["dizi","dunya"]}, "skip" ile dışla.
- Tekilleştirme: aynı internalName için en yüksek sürüm; eşitlikte
  dedupe.sourcePriority = [mrc, turk, pars, spor, karayel, adult].
- Kaynak sürümü artmadığı halde dosya içeriği değişirse yayın sürümünü +1 artır.
- Dosya adları ASCII'ye çevrilir (ç→c, ğ→g, ı→i, İ→I, ö→o, ş→s, ü→u), çakışmada -2 eki.
- Tüm dosyalar UTF-8 + LF, JSON'lar 2 boşluk girintili ve ensure_ascii=False.
- .gitattributes: "* text=auto eol=lf", "*.cmd text eol=crlf", "*.cs3 binary" (hash bozulmasın).
- .gitignore: __pycache__, *.pyc, *.tmp, reports/ (rapor üretilir, depoyu kirletmesin).
- pamuk.cmd: "@echo off / chcp 65001 >nul / setlocal / python "%~dp0tools\pamuk.py" %* / endlocal"
  ve CRLF satır sonuyla yazılmalı.
- AGENTS.md: her oturum başında `python tools/pamuk.py check` çalıştır, sonucu kullanıcıya özetle,
  değişiklik varsa onay iste; onay olmadan sync/build/push yapma; üretilen dosyaları elle düzenleme;
  her revizyonda "KULLANMA KLAVUZU ve FİNAL PROMTU.md" dosyasını güncelle.

İŞ AKIŞI
1) İskeleti ve config dosyalarını oluştur. 2) `check` ile 329 kaydın okunduğunu doğrula.
3) `sync` ile tüm .cs3 dosyalarını indir. 4) `build` + `verify` çalıştır (582 kayıt, hash'ler tutarlı).
5) git init -b main, .gitattributes/.gitignore ekle, commit et, origin'e push et.
6) Push sonrası canlı linkleri curl ile doğrula (repo.json 200) ve bir .cs3 dosyasının
   sha256'sını manifestle karşılaştır.

Beklenen sonuç: 6 kaynak, 329 aynalanan eklenti, 285 benzersiz kayıt, 9 liste
(ana + 8 başlık), çalışan canlı raw linkleri ve check→onay→sync→build→verify akışı.
```
