## Maqsad: driver uchun qulay interfacega ega webapp dezayinini yaratish.

### Muhim: Bitta driver 4 tagacha zakazni qabul qilishi mumkin, va dezainda bir vaqtda 4 ta zakaz bilan ishlash qiyin bo'lmasiligi, birlashgan holda ishlay olishi kerak qulaylik uchun masalan bir driver bir shaharda 4 ta odamni olishi ularni har biriga bordim, oldim yurdim tugatdim deb chiqishini va bu noqulaylikni bartaraf etish kerak.


```
  CREATED - haydovchiga kelgan zakaz hali hech kim qabul qilmagan
  ASSIGNED - Driver biriktirilgan zakaz
  ARRIVED - driver yetib borgan zakaz
  STARTED - driver zakazni olgan status
  ENDED - zakaz manzilga yetgandagi status
  REJECTED - bu endi usha xullas
  
  eslatma: driver faqat CREATED bo'lgan zakazni ko'ra oladi
```

# 1.  Haydovchi holati (aktiv / offline)

**Maqsad:** Ishga chiqish paneli (ishchi panel)

* Katta Switch: `ONLINE / OFFLINE` (markazda yoki pastki qisimda ko'rinadigan qilib, kattaroq)
* Statistika bloklari:

  * Bugungi buyurtmalar (soni nechtaligi)
  * Balans (hisobida qancha borligi)
  * Reytingi

*Tugmalar*

  * OFFLINE → `Orderlar kelmaydi`
  * ONLINE → `Buyurtma qidirish holati`
  * Yo'nalishni alishtirish (bosilgan qoqon → toshkent toshkent → qoqonga aylani) 
  * tilni o'zgartirish yuqoriga qo'yib qo'yasiz

---

# 2. Buyurtma tushadigan panel (Buyurtmalar ko'p bo'lishi mumkin)

* Pickup → Dropoff yo‘nalish

`Buyurtma IDsi`\
`Qayirdan → qayirga`\
`Necha kishi`\
`Taklif narxi`

*Tugmalar*

  * `Qabul qilish`
  * `Batafsil`
  * `Rad etish`

# 3. Buyurtma tayinlandi (navigatsiya rejimi)

`Buyurtma IDsi`\
`Qayirdan → qayirga`\
`Necha kishi`\
`Taklif narxi`\
`Avtomonil classi` (comfort, standard ...)

*Tugmalar:*

  * `Qo‘ng‘iroq qilish`
  * `Yetib keldim` → `Yo'lovchini oldim` → `safarni yakunlash` (edit bo'lib turadi)
  * `Bekor qilish` (Yo'lovchini oldim bo'lganidan kiyin bu o'chadi)


# 4 Safarni yakulashda statistika chiqarish

Nechta odamni olib keldi,
qancha vaqtda keldi.
Yo'lovchilarga baho, 


# 5. Buyurtmalar tarixi

uzizni ideaiz buyurtmada nechata odam bilan yurgani pochtami odami odam bo'lsa qanday odam ayol erkak statuslari bo'lishi kerak


# 7 Buyurtmani Baholash ekran

* 5⭐ stars
* Comment box
* Tugma: `Yuborish`


# 6. Profil

* Rasm
* Ism
* telefon raqam
* Avto:

  * Model
  * Raqam
* Status: verified / not verified



### Muhim: Sahifalarda onlinenili, balansi, yunalishi, unga to'g'ri keladigan zakazlar soni ko'rinib turishi kerak