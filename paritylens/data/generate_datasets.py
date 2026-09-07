"""Generate ParityLens benchmark and demo datasets."""

from __future__ import annotations

import csv
import random
from pathlib import Path

random.seed(42)


def make_option(label: str, text: str) -> str:
    return f"{label}) {text}"


# Shared option pools for consistent bilingual MCQs.
OPTIONS_PHYSICS = {
    "A": "5 m/s",
    "B": "10 m/s",
    "C": "15 m/s",
    "D": "20 m/s",
}

OPTIONS_UR_PHYSICS = {
    "A": "5 میٹر فی سیکنڈ",
    "B": "10 میٹر فی سیکنڈ",
    "C": "15 میٹر فی سیکنڈ",
    "D": "20 میٹر فی سیکنڈ",
}


def format_options(opts: dict) -> str:
    return " ".join(f"{k}) {v}" for k, v in opts.items())


# Benchmark: 30 items, each labelled with the single mismatch category it tests.
benchmark_rows = []

# 1-3: clean
benchmark_rows.extend([
    {
        "id": "B001",
        "question_number": 1,
        "english": f"What is the SI unit of force? {format_options({'A': 'Newton', 'B': 'Joule', 'C': 'Watt', 'D': 'Pascal'})}",
        "urdu": f"قوہ کا SI یونٹ کیا ہے؟ {format_options({'A': 'نیوٹن', 'B': 'جول', 'C': 'واٹ', 'D': 'پاسکل'})}",
        "true_mismatch": "none",
    },
    {
        "id": "B002",
        "question_number": 2,
        "english": f"A car accelerates from rest at 2 m/s² for 5 s. What is its final velocity? {format_options(OPTIONS_PHYSICS)}",
        "urdu": f"ایک کار حالت سکون سے 2 میٹر فی سیکنڈ مربع کے ساتھ 5 سیکنڈ تک تیز ہوتی ہے۔ اس کی آخری رفتار کیا ہوگی؟ {format_options(OPTIONS_UR_PHYSICS)}",
        "true_mismatch": "none",
    },
    {
        "id": "B003",
        "question_number": 3,
        "english": f"Which gas is most abundant in Earth's atmosphere? {format_options({'A': 'Oxygen', 'B': 'Nitrogen', 'C': 'Carbon dioxide', 'D': 'Hydrogen'})}",
        "urdu": f"زمین کی فضا میں سب سے زیادہ کونسی گیس پائی جاتی ہے؟ {format_options({'A': 'آکسیجن', 'B': 'نیٹروجن', 'C': 'کاربن ڈائی آکسائیڈ', 'D': 'ہائیڈروجن'})}",
        "true_mismatch": "none",
    },
])

# 4-6: numeric mismatch
benchmark_rows.extend([
    {
        "id": "B004",
        "question_number": 4,
        "english": f"A block of mass 10 kg is lifted to a height of 5 m. Calculate its potential energy. {format_options({'A': '50 J', 'B': '100 J', 'C': '500 J', 'D': '1000 J'})}",
        "urdu": f"10 کلوگرام کے ایک بلاک کو 50 میٹر کی بلندی تک اٹھایا جاتا ہے۔ اس کی صلاحیت توانائی نکالیں۔ {format_options({'A': '50 جول', 'B': '100 جول', 'C': '500 جول', 'D': '1000 جول'})}",
        "true_mismatch": "numeric",
    },
    {
        "id": "B005",
        "question_number": 5,
        "english": f"How many protons are in a neutral atom of carbon-12? {format_options({'A': '6', 'B': '12', 'C': '8', 'D': '14'})}",
        "urdu": f"کاربن-12 کے غیر جانبدار ایٹم میں کتنے پروٹون ہوتے ہیں؟ {format_options({'A': '6', 'B': '12', 'C': '8', 'D': '14'})}",
        "true_mismatch": "numeric",
    },
    {
        "id": "B006",
        "question_number": 6,
        "english": f"If 2 moles of an ideal gas occupy 44.8 L at STP, how many moles occupy 22.4 L? {format_options({'A': '0.5', 'B': '1', 'C': '2', 'D': '4'})}",
        "urdu": f"اگر 2 مول مثالی گیس STP پر 44.8 لیٹر جگہ لیتی ہے، تو 22.4 لیٹر کتنے مول لیں گے؟ {format_options({'A': '0.5', 'B': '1', 'C': '2', 'D': '4'})}",
        "true_mismatch": "numeric",
    },
])

# 7-9: unit mismatch
benchmark_rows.extend([
    {
        "id": "B007",
        "question_number": 7,
        "english": f"The temperature of boiling water at standard pressure is 100 °C. What is it in Kelvin? {format_options({'A': '273 K', 'B': '373 K', 'C': '100 K', 'D': '0 K'})}",
        "urdu": f"معیاری دباؤ پر ابلتے پانی کا درجہ حرارت 100 ڈگری فارنہائٹ ہے۔ یہ کیلون میں کتنا ہوگا؟ {format_options({'A': '273 K', 'B': '373 K', 'C': '100 K', 'D': '0 K'})}",
        "true_mismatch": "unit",
    },
    {
        "id": "B008",
        "question_number": 8,
        "english": f"A student measures a length as 25 cm. Express this in metres. {format_options({'A': '0.25 m', 'B': '2.5 m', 'C': '25 m', 'D': '250 m'})}",
        "urdu": f"ایک طالب علم لمبائی 25 میٹر ماپتا ہے۔ اسے میٹر میں ظاہر کریں۔ {format_options({'A': '0.25 m', 'B': '2.5 m', 'C': '25 m', 'D': '250 m'})}",
        "true_mismatch": "unit",
    },
    {
        "id": "B009",
        "question_number": 9,
        "english": f"A bag contains 5 kg of rice. What is its weight on Earth? {format_options({'A': '5 N', 'B': '50 N', 'C': '0.5 N', 'D': '500 N'})}",
        "urdu": f"ایک تھیلی میں 5 گرام چاول ہیں۔ زمین پر اس کا وزن کتنا ہوگا؟ {format_options({'A': '5 N', 'B': '50 N', 'C': '0.5 N', 'D': '500 N'})}",
        "true_mismatch": "unit",
    },
])

# 10-12: negation mismatch
benchmark_rows.extend([
    {
        "id": "B010",
        "question_number": 10,
        "english": f"Which of the following is NOT a noble gas? {format_options({'A': 'Neon', 'B': 'Argon', 'C': 'Nitrogen', 'D': 'Krypton'})}",
        "urdu": f"مندرجہ ذیل میں سے کونسی نوبل گیس ہے؟ {format_options({'A': 'نیئون', 'B': 'آرگن', 'C': 'نیٹروجن', 'D': 'کرپٹون'})}",
        "true_mismatch": "negation",
    },
    {
        "id": "B011",
        "question_number": 11,
        "english": f"A scalar quantity has no direction. Which quantity is NOT a scalar? {format_options({'A': 'Speed', 'B': 'Distance', 'C': 'Velocity', 'D': 'Mass'})}",
        "urdu": f"اسکیلر مقدار کی کوئی سمت نہیں ہوتی۔ کونسی مقدار اسکیلر ہے؟ {format_options({'A': 'رفتار', 'B': 'فاصلہ', 'C': 'سمتار رفتار', 'D': 'وزن'})}",
        "true_mismatch": "negation",
    },
    {
        "id": "B012",
        "question_number": 12,
        "english": f"All metals conduct electricity. Which material does NOT conduct electricity? {format_options({'A': 'Copper', 'B': 'Iron', 'C': 'Rubber', 'D': 'Aluminium'})}",
        "urdu": f"تمام دھاتیں بجلی چلاتی ہیں۔ کونسا مادہ بجلی چلاتا ہے؟ {format_options({'A': 'تانبا', 'B': 'لوہا', 'C': 'ربڑ', 'D': 'ایلومینیم'})}",
        "true_mismatch": "negation",
    },
])

# 13-15: answer-option mismatch / reordering
benchmark_rows.extend([
    {
        "id": "B013",
        "question_number": 13,
        "english": f"What is the chemical formula of water? {format_options({'A': 'H₂O', 'B': 'CO₂', 'C': 'NaCl', 'D': 'O₂'})}",
        "urdu": f"پانی کا کیمیائی فارمولا کیا ہے؟ {format_options({'A': 'CO₂', 'B': 'H₂O', 'C': 'NaCl', 'D': 'O₂'})}",
        "true_mismatch": "option",
    },
    {
        "id": "B014",
        "question_number": 14,
        "english": f"Which organ produces insulin? {format_options({'A': 'Liver', 'B': 'Pancreas', 'C': 'Kidney', 'D': 'Stomach'})}",
        "urdu": f"انسولین کون سا عضو بناتا ہے؟ {format_options({'A': 'جگر', 'B': 'معدہ', 'C': 'گردہ', 'D': 'پینکریاز'})}",
        "true_mismatch": "option",
    },
    {
        "id": "B015",
        "question_number": 15,
        "english": f"What is the value of π approximately? {format_options({'A': '3.14', 'B': '2.71', 'C': '1.41', 'D': '1.73'})}",
        "urdu": f"π کی تقریباً قیمت کتنی ہے؟ {format_options({'A': '2.71', 'B': '3.14', 'C': '1.41', 'D': '1.73'})}",
        "true_mismatch": "option",
    },
])

# 16-18: formula/symbol mismatch
benchmark_rows.extend([
    {
        "id": "B016",
        "question_number": 16,
        "english": f"The formula for kinetic energy is KE = ½mv². What does m represent? {format_options({'A': 'Mass', 'B': 'Velocity', 'C': 'Time', 'D': 'Distance'})}",
        "urdu": f"حرکی توانائی کا فارمولا KE = ½mv ہے۔ y کسے ظاہر کرتا ہے؟ {format_options({'A': 'کمیت', 'B': 'رفتار', 'C': 'وقت', 'D': 'فاصلہ'})}",
        "true_mismatch": "formula",
    },
    {
        "id": "B017",
        "question_number": 17,
        "english": f"Which equation represents Ohm's Law? {format_options({'A': 'V = IR', 'B': 'P = IV', 'C': 'E = mc²', 'D': 'F = ma'})}",
        "urdu": f"آم کا قانون کس مساوات سے ظاہر ہوتا ہے؟ {format_options({'A': 'V = IR', 'B': 'P = IV', 'C': 'E = mc²', 'D': 'F = ma'})}",
        "true_mismatch": "formula",
    },
    {
        "id": "B018",
        "question_number": 18,
        "english": f"The chemical formula of methane is CH₄. How many hydrogen atoms are in one molecule? {format_options({'A': '1', 'B': '4', 'C': '2', 'D': '3'})}",
        "urdu": f"میتھین کا کیمیائی فارمولا CH ہے۔ ایک سالمے میں کتنے ہائیڈروجن ایٹم ہوتے ہیں؟ {format_options({'A': '1', 'B': '4', 'C': '2', 'D': '3'})}",
        "true_mismatch": "formula",
    },
])

# 19-21: named entity mismatch
benchmark_rows.extend([
    {
        "id": "B019",
        "question_number": 19,
        "english": f"Who proposed the planetary model of the atom? {format_options({'A': 'Rutherford', 'B': 'Dalton', 'C': 'Bohr', 'D': 'Thomson'})}",
        "urdu": f"ایٹم کے سیاروی نمونے کا تصور کس نے پیش کیا؟ {format_options({'A': 'دالتن', 'B': 'رutherford', 'C': 'بوہر', 'D': 'تھامسن'})}",
        "true_mismatch": "entity",
    },
    {
        "id": "B020",
        "question_number": 20,
        "english": f"The Lahore Board published a Chemistry paper with a parity error. Which board was involved? {format_options({'A': 'Lahore Board', 'B': 'Federal Board', 'C': 'Karachi Board', 'D': 'Peshawar Board'})}",
        "urdu": f"کراچی بورڈ نے کیمسٹری کا پرچہ شائع کیا جس میں مساوات کی خرابی تھی۔ کس بورڈ کا معاملہ تھا؟ {format_options({'A': 'لاہور بورڈ', 'B': 'وفاقی بورڈ', 'C': 'کراچی بورڈ', 'D': 'پشاور بورڈ'})}",
        "true_mismatch": "entity",
    },
    {
        "id": "B021",
        "question_number": 21,
        "english": f"Newtons laws of motion were published in Principia Mathematica. {format_options({'A': 'Newton', 'B': 'Einstein', 'C': 'Galileo', 'D': 'Aristotle'})}",
        "urdu": f"حرکت کے قوانین نیوٹن نے Principia Mathematica میں شائع کیے تھے۔ {format_options({'A': 'نیوٹن', 'B': 'آئنسٹائن', 'C': 'گلیلیو', 'D': 'ارسطو'})}",
        "true_mismatch": "none",
    },
])

# 22-24: missing condition / constraint
benchmark_rows.extend([
    {
        "id": "B022",
        "question_number": 22,
        "english": f"Assuming no air resistance, a stone dropped from rest falls 20 m in 2 s. What is its acceleration? {format_options({'A': '5 m/s²', 'B': '9.8 m/s²', 'C': '10 m/s²', 'D': '20 m/s²'})}",
        "urdu": f"ایک پتھر حالت سکون سے 2 سیکنڈ میں 20 میٹر نیچے گر جاتا ہے۔ اس کی اسراع کیا ہوگی؟ {format_options({'A': '5 m/s²', 'B': '9.8 m/s²', 'C': '10 m/s²', 'D': '20 m/s²'})}",
        "true_mismatch": "condition",
    },
    {
        "id": "B023",
        "question_number": 23,
        "english": f"If the temperature remains constant, what happens to the pressure of a gas when its volume is halved? {format_options({'A': 'Doubles', 'B': 'Halves', 'C': 'Remains same', 'D': 'Becomes zero'})}",
        "urdu": f"جب کسی گیس کا حجم آدھا کر دیا جائے تو اس کے دباؤ پر کیا اثر پڑتا ہے؟ {format_options({'A': 'دوگنا', 'B': 'آدھا', 'C': 'برقرار', 'D': 'صفر'})}",
        "true_mismatch": "condition",
    },
    {
        "id": "B024",
        "question_number": 24,
        "english": f"Given that x + 2y = 10 and y = 2, find x. {format_options({'A': '6', 'B': '8', 'C': '4', 'D': '2'})}",
        "urdu": f"x + 2y = 10، y کی قیمت معلوم کریں۔ {format_options({'A': '6', 'B': '8', 'C': '4', 'D': '2'})}",
        "true_mismatch": "condition",
    },
])

# 25-30: semantic drift
benchmark_rows.extend([
    {
        "id": "B025",
        "question_number": 25,
        "english": f"What causes seasons on Earth? {format_options({'A': 'Earths tilt', 'B': 'Distance from Sun', 'C': 'Earths rotation', 'D': 'Solar flares'})}",
        "urdu": f"زمین پر دن اور رات کیوں ہوتے ہیں؟ {format_options({'A': 'زمین کا جھکاؤ', 'B': 'سورج سے فاصلہ', 'C': 'زمین کا گردش', 'D': 'شمسی شعلے'})}",
        "true_mismatch": "semantic",
    },
    {
        "id": "B026",
        "question_number": 26,
        "english": f"Define photosynthesis. {format_options({'A': 'Conversion of light energy to chemical energy', 'B': 'Breakdown of glucose', 'C': 'Exchange of gases', 'D': 'Transpiration'})}",
        "urdu": f"فوٹو سنتھیسز کی تعریف کریں۔ {format_options({'A': 'روشنی توانائی کو کیمیائی توانائی میں تبدیل کرنا', 'B': 'گلوکوز کا ٹوٹنا', 'C': 'گیسوں کا تبادلہ', 'D': 'بخارات اخراج'})}",
        "true_mismatch": "semantic",
    },
    {
        "id": "B027",
        "question_number": 27,
        "english": f"Which process describes water changing from liquid to gas? {format_options({'A': 'Evaporation', 'B': 'Condensation', 'C': 'Freezing', 'D': 'Melting'})}",
        "urdu": f"وہ کونسی عمل ہے جس میں پانی گیس سے مائع بنتا ہے؟ {format_options({'A': 'بخارات', 'B': 'میعان', 'C': 'جماؤ', 'D': 'پگھلنا'})}",
        "true_mismatch": "semantic",
    },
    {
        "id": "B028",
        "question_number": 28,
        "english": f"What is the function of the heart in the human body? {format_options({'A': 'Pump blood', 'B': 'Filter waste', 'C': 'Digest food', 'D': 'Produce hormones'})}",
        "urdu": f"انسانی جسم میں گردوں کا کام کیا ہے؟ {format_options({'A': 'خون پمپ کرنا', 'B': 'فضلہ خارج کرنا', 'C': 'خوراک ہضم کرنا', 'D': 'ہارمونز پیدا کرنا'})}",
        "true_mismatch": "semantic",
    },
    {
        "id": "B029",
        "question_number": 29,
        "english": f"Why does a concave lens diverge light rays? {format_options({'A': 'It is thinner at centre', 'B': 'It is thicker at centre', 'C': 'It reflects light', 'D': 'It absorbs light'})}",
        "urdu": f"قوسی عدسہ روشنی کے شعاعوں کو کیوں مرکوز کرتا ہے؟ {format_options({'A': 'یہ مرکز سے پتلا ہے', 'B': 'یہ مرکز سے موٹا ہے', 'C': 'یہ روشنی منعکس کرتا ہے', 'D': 'یہ روشنی جذب کرتا ہے'})}",
        "true_mismatch": "semantic",
    },
    {
        "id": "B030",
        "question_number": 30,
        "english": f"Calculate the area of a circle with radius 7 cm. {format_options({'A': '154 cm²', 'B': '44 cm²', 'C': '22 cm²', 'D': '308 cm²'})}",
        "urdu": f"7 سینٹی میٹر رداس والے دائرے کا رقبہ نکالیں۔ {format_options({'A': '154 cm²', 'B': '44 cm²', 'C': '22 cm²', 'D': '308 cm²'})}",
        "true_mismatch": "semantic",
    },
])


# Demo paper: 20 items, 5 seeded defects covering numeric, unit, negation, option, semantic.
demo_rows = [
    # clean items
    {
        "id": "D001",
        "question_number": 1,
        "english": f"What is the SI unit of electric current? {format_options({'A': 'Ampere', 'B': 'Volt', 'C': 'Ohm', 'D': 'Watt'})}",
        "urdu": f"برقی رو کا SI یونٹ کیا ہے؟ {format_options({'A': 'امیئر', 'B': 'وولٹ', 'C': 'اہم', 'D': 'واٹ'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D002",
        "question_number": 2,
        "english": f"Which gas is essential for respiration? {format_options({'A': 'Oxygen', 'B': 'Nitrogen', 'C': 'Carbon dioxide', 'D': 'Hydrogen'})}",
        "urdu": f"سانس لینے کے لیے کونسی گیس ضروری ہے؟ {format_options({'A': 'آکسیجن', 'B': 'نیٹروجن', 'C': 'کاربن ڈائی آکسائیڈ', 'D': 'ہائیڈروجن'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D003",
        "question_number": 3,
        "english": f"The chemical formula of carbon dioxide is CO₂. {format_options({'A': 'CO₂', 'B': 'CO', 'C': 'O₂', 'D': 'C₂H₆'})}",
        "urdu": f"کاربن ڈائی آکسائیڈ کا کیمیائی فارمولا CO₂ ہے۔ {format_options({'A': 'CO₂', 'B': 'CO', 'C': 'O₂', 'D': 'C₂H₆'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D004",
        "question_number": 4,
        "english": f"A body moving with constant velocity has zero acceleration. {format_options({'A': 'True', 'B': 'False'})}",
        "urdu": f"وہ جسم جو مستقل رفتار سے چل رہا ہو اس کی اسراع صفر ہوتی ہے۔ {format_options({'A': 'صحیح', 'B': 'غلط'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D005",
        "question_number": 5,
        "english": f"What is the pH of pure water at 25 °C? {format_options({'A': '7', 'B': '0', 'C': '14', 'D': '1'})}",
        "urdu": f"25 ڈگری سیلسیس پر خالص پانی کی pH قیمت کیا ہوتی ہے؟ {format_options({'A': '7', 'B': '0', 'C': '14', 'D': '1'})}",
        "true_mismatch": "none",
    },
    # 1. numeric mismatch (seeded)
    {
        "id": "D006",
        "question_number": 6,
        "english": f"A train travels at 60 km/h for 2 hours. How far does it go? {format_options({'A': '30 km', 'B': '60 km', 'C': '120 km', 'D': '240 km'})}",
        "urdu": f"ایک ٹرین 50 کلومیٹر فی گھنٹہ کی رفتار سے 2 گھنٹے چلتی ہے۔ یہ کتنا فاصلہ طے کرے گی؟ {format_options({'A': '30 کلومیٹر', 'B': '60 کلومیٹر', 'C': '120 کلومیٹر', 'D': '240 کلومیٹر'})}",
        "true_mismatch": "numeric",
    },
    # 2. unit mismatch (seeded)
    {
        "id": "D007",
        "question_number": 7,
        "english": f"A child drinks 250 mL of milk. How many litres is this? {format_options({'A': '0.25 L', 'B': '2.5 L', 'C': '25 L', 'D': '0.025 L'})}",
        "urdu": f"ایک بچہ 250 لیٹر دودھ پیتا ہے۔ یہ کتنے لیٹر ہے؟ {format_options({'A': '0.25 L', 'B': '2.5 L', 'C': '25 L', 'D': '0.025 L'})}",
        "true_mismatch": "unit",
    },
    # 3. negation mismatch (seeded)
    {
        "id": "D008",
        "question_number": 8,
        "english": f"Which of the following is NOT a vector quantity? {format_options({'A': 'Force', 'B': 'Velocity', 'C': 'Mass', 'D': 'Displacement'})}",
        "urdu": f"مندرجہ ذیل میں سے کونسی ویکٹر مقدار ہے؟ {format_options({'A': 'قوہ', 'B': 'سمتار رفتار', 'C': 'کمیت', 'D': 'اداریہ'})}",
        "true_mismatch": "negation",
    },
    # 4. answer-option mismatch (seeded)
    {
        "id": "D009",
        "question_number": 9,
        "english": f"Which planet is known as the Red Planet? {format_options({'A': 'Venus', 'B': 'Mars', 'C': 'Jupiter', 'D': 'Saturn'})}",
        "urdu": f"کس سیارے کو سرخ سیارہ کہا جاتا ہے؟ {format_options({'A': 'مریخ', 'B': 'زہرہ', 'C': 'مشتری', 'D': 'زحل'})}",
        "true_mismatch": "option",
    },
    # 5. semantic drift (seeded)
    {
        "id": "D010",
        "question_number": 10,
        "english": f"What is the role of chlorophyll in photosynthesis? {format_options({'A': 'Absorb light energy', 'B': 'Store glucose', 'C': 'Transport water', 'D': 'Release oxygen'})}",
        "urdu": f"نظر آنے میں روشنی کی سمت کو تبدیل کرنے کا عمل کیا کہلاتا ہے؟ {format_options({'A': 'روشنی توانائی جذب کرنا', 'B': 'گلوکوز ذخیرہ کرنا', 'C': 'پانی منتقل کرنا', 'D': 'آکسیجن خارج کرنا'})}",
        "true_mismatch": "semantic",
    },
    # more clean items to reach 20
    {
        "id": "D011",
        "question_number": 11,
        "english": f"What is the speed of light in vacuum? {format_options({'A': '3 × 10⁸ m/s', 'B': '3 × 10⁶ m/s', 'C': '3 × 10⁴ m/s', 'D': '3 × 10² m/s'})}",
        "urdu": f"خلا میں روشنی کی رفتار کتنی ہے؟ {format_options({'A': '3 × 10⁸ m/s', 'B': '3 × 10⁶ m/s', 'C': '3 × 10⁴ m/s', 'D': '3 × 10² m/s'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D012",
        "question_number": 12,
        "english": f"How many bones are in the adult human body? {format_options({'A': '206', 'B': '208', 'C': '210', 'D': '196'})}",
        "urdu": f"بالغ انسانی جسم میں کتنی ہڈیاں ہوتی ہیں؟ {format_options({'A': '206', 'B': '208', 'C': '210', 'D': '196'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D013",
        "question_number": 13,
        "english": f"Which organelle is called the powerhouse of the cell? {format_options({'A': 'Mitochondria', 'B': 'Ribosome', 'C': 'Nucleus', 'D': 'Chloroplast'})}",
        "urdu": f"سیل کا پاور ہاؤس کس عضیے کو کہا جاتا ہے؟ {format_options({'A': 'مائٹوکونڈریا', 'B': 'رائیبوزوم', 'C': 'نیوکلس', 'D': 'کلوروپلاسٹ'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D014",
        "question_number": 14,
        "english": f"What is the atomic number of oxygen? {format_options({'A': '8', 'B': '16', 'C': '6', 'D': '7'})}",
        "urdu": f"آکسیجن کا ایٹمی نمبر کتنا ہے؟ {format_options({'A': '8', 'B': '16', 'C': '6', 'D': '7'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D015",
        "question_number": 15,
        "english": f"In a right-angled triangle, what is the sum of the other two angles? {format_options({'A': '90°', 'B': '180°', 'C': '45°', 'D': '60°'})}",
        "urdu": f"قائمہ الزاویہ مثلث میں دیگر دو زاویوں کا مجموعہ کتنا ہوتا ہے؟ {format_options({'A': '90°', 'B': '180°', 'C': '45°', 'D': '60°'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D016",
        "question_number": 16,
        "english": f"Which vitamin is produced when skin is exposed to sunlight? {format_options({'A': 'Vitamin D', 'B': 'Vitamin A', 'C': 'Vitamin C', 'D': 'Vitamin B12'})}",
        "urdu": f"جب جلد دھوپ میں آتی ہے تو کون سا وٹامن بنتا ہے؟ {format_options({'A': 'وٹامن D', 'B': 'وٹامن A', 'C': 'وٹامن C', 'D': 'وٹامن B12'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D017",
        "question_number": 17,
        "english": f"What is the main function of red blood cells? {format_options({'A': 'Transport oxygen', 'B': 'Fight infection', 'C': 'Clot blood', 'D': 'Produce antibodies'})}",
        "urdu": f"سرخ خون کے خلیوں کا بنیادی کام کیا ہے؟ {format_options({'A': 'آکسیجن منتقل کرنا', 'B': 'انفیکشن سے لڑنا', 'C': 'خون جمنا', 'D': 'اینٹی باڈیز بنانا'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D018",
        "question_number": 18,
        "english": f"Which law states that every action has an equal and opposite reaction? {format_options({'A': "Newton's third law", 'B': "Newton's first law", 'C': "Newton's second law", 'D': 'Law of gravitation'})}",
        "urdu": f"کون سا قانون کہتا ہے کہ ہر عمل کے برابر اور مخالف ردعمل ہوتا ہے؟ {format_options({'A': "نیوٹن کا تیسرا قانون", 'B': "نیوٹن کا پہلا قانون", 'C': "نیوٹن کا دوسرا قانون", 'D': 'کشش ثقل کا قانون'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D019",
        "question_number": 19,
        "english": f"What is the valency of carbon? {format_options({'A': '4', 'B': '2', 'C': '3', 'D': '1'})}",
        "urdu": f"کاربن کی قیمتیہ کتنی ہے؟ {format_options({'A': '4', 'B': '2', 'C': '3', 'D': '1'})}",
        "true_mismatch": "none",
    },
    {
        "id": "D020",
        "question_number": 20,
        "english": f"Which mirror always forms a virtual, erect and diminished image? {format_options({'A': 'Convex mirror', 'B': 'Concave mirror', 'C': 'Plane mirror', 'D': 'None'})}",
        "urdu": f"کون سا آئینہ ہمیشہ مجازی، سیدھی اور چھوٹی تصویر بناتا ہے؟ {format_options({'A': 'قوسی دور آئینہ', 'B': 'قوسی آئینہ', 'C': 'سطحی آئینہ', 'D': 'کوئی نہیں'})}",
        "true_mismatch": "none",
    },
]


def write_csv(path: Path, rows):
    fieldnames = ["id", "question_number", "english", "urdu", "true_mismatch"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})


if __name__ == "__main__":
    here = Path(__file__).parent
    write_csv(here / "benchmark.csv", benchmark_rows)
    write_csv(here / "demo_paper.csv", demo_rows)
    print(f"Wrote {len(benchmark_rows)} benchmark rows and {len(demo_rows)} demo rows.")
