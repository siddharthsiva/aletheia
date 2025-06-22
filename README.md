# **Aletheia – Clarity in Care**  
> _Because your health should not be confusing_

![ChatGPT Image Jun 22, 2025, 07_09_45 AM](https://github.com/user-attachments/assets/2dfb97e0-0cde-4e7a-abdb-35cd32f04597)

---

## ✨ Inspiration  
Healthcare is too often a maze of hidden fees, cryptic jargon, and opaque decisions. Surprise bills, misunderstood meds, and denied claims erode trust. **Aletheia** (“ ἀλήθεια ” = *truth*) exists to make clarity the default and profit-driven ambiguity impossible.

---

## 💡 What Aletheia Does

| Pillars | At-a-Glance |
|---------|-------------|
| **📄 Document Parsing** | Upload medical files—Aletheia extracts diagnoses, allergies & history into a living profile. |
| **💊 Medication Guardian** | Log pills, receive reminders, and get immediate next-step advice for missed doses (urgent-condition aware). |
| **📸 Pill Identifier** | Snap a photo, we ID the pill (FDA NDC cross-check) and explain ingredients & effects in plain English. |
| **🛡️ Insurance Trust Index** | Rates insurers by controversies, verified reviews & news; recommends better matches for *your* context. |
| **🗣️ Transparent Health Assistant** | Conversational AI that **shows its chain-of-thought** and can escalate to a real clinician via Slack. |

---

## 🏗️ How We Built It
1. **Multi-Agent Backend** – Dedicated agents for parsing, pill ID, insurance scoring & advice.  
2. **Shared Secure Context** – Encrypted health profile each agent can query, never duplicate.  
3. **Trusted APIs** – FDA open data, Google Gemini, Slack API for doctor pings.  
4. **Streamlit Front-End** – Drag-and-drop uploads, pill logs, transparent chat.  

---

## 🚧 Challenges
- **Orchestrating specialists** without overlap or contradiction.  
- Balancing **radical transparency** with HIPAA-grade privacy.  
- Continuous filtering to keep every AI answer **accurate & non-misleading**.  

---

## 🏆 Accomplishments
- Functional **hospital-style AI network** parsing real docs & pill images.  
- **Last-minute pivot** while keeping mission impact intact.  
- Full **AI thought-visibility**—users see the reasoning we see.

---

## 📚 What We Learned
- Clear domain boundaries are vital for **multi-agent orchestration**.  
- Personal context makes or breaks meaningful health advice.  
- **Transparency breeds trust**—people love seeing the “why”.  
- AI + **human experts** is the safety net every health tool needs.

---

## 🚀 Roadmap
- Deeper integrations with providers & pharmacists.  
- Broaden trusted-data pipelines: more medical & insurance datasets.  
- Sleeker UI focused on one-tap clarity and control.  
- Become the **gold standard** in transparent, personalized, life-first care.

---

## 🛠️ Built With
| Category | Tech |
|----------|------|
| **Language / Runtime** | Python 3.12 |
| **UI** | Streamlit |
| **AI / LLM** | Google Gemini 2.5 Flash + Letta Multi-model agents |
| **Multi-Agent Toolkit** | **Custom orchestration layer** |
| **Data Sources** | FDA Open Drug Data, Google Search, News APIs |
| **Messaging** | Slack API |
| **Infra / DevOps** | Vercel Blob Storage, GitHub Actions |

---

## 🔧 Installation

```bash
git clone https://github.com/siddharthsiva/aletheia.git
cd aletheia
pip install -r requirements.txt
streamlit run app.py            # or whatever the entry file is
