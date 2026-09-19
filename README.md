# MY Office and Home PC Sync 🚀
> Automated Synchronization between Office PC and Home PC for **Factify Shorts Automation** (`@FactifyDailyShorts`).

---

## 📌 How to Sync Daily (দৈনিক সিঙ্ক করার নিয়ম)

### 🏢 অফিসে কাজ শেষে (Office PC -> GitHub):
অফিসে কাজ শেষ হলে শুধু এই কমান্ডগুলো চালান:
```bash
git add .
git commit -m "Office update: [আজকে কি কাজ করলেন সংক্ষেপে লিখুন]"
git push origin main
```

### 🏠 বাসায় এসে (GitHub -> Home PC):
বাসায় এসে নতুন আপডেট নামাতে শুধু এই কমান্ডটি দিন:
```bash
git pull origin main
```
*(অথবা Antigravity-কে শুধু বলবেন: "GitHub theke update pull koro")*

---

## 📂 Project Structure (ফাইল বিবরণ)
* `PROGRESS.md` - অফিস এবং বাসায় কি কি কাজ হলো তার লাইভ ট্র্যাকার।
* `pipeline/` - Factify Shorts তৈরির অটোমেশন স্ক্রিপ্ট ও টপিক ডাটাবেস।
* `.gitignore` - বড় ভিডিও ফাইল ও সিক্রেট কি যেন গিটহাবে আপলোড না হয় তার ফিল্টার।
