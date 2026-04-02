import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      welcome: "Welcome to Rentora",
      subtitle: "Premium property rentals made effortless.",
      login: "Login",
      signup: "Sign Up",
      register_title: "Create an Account",
      register_subtitle: "Join the Rentora community today.",
      email_phone: "Email or Phone Number",
      password: "Password",
      role_tenant: "Tenant",
      role_owner: "Owner",
      already_have_account: "Already have an account?",
      dont_have_account: "Don't have an account?",
      verify_otp: "Verify OTP",
      otp_sent: "Enter the code sent to your device",
      verify_btn: "Verify & Continue",
      dashboard: "Dashboard",
      browse_listings: "Browse Listings",
      add_property: "Add Property",
      profile: "Profile",
      logout: "Logout",
      // ... more to be added
    }
  },
  hi: {
    translation: {
      welcome: "Rentora में आपका स्वागत है",
      subtitle: "प्रीमियम संपत्ति किराए पर लेना अब आसान।",
      login: "लॉगिन",
      signup: "साइन अप",
      register_title: "अकाउंट बनाएं",
      register_subtitle: "आज ही Rentora समुदाय से जुड़ें।",
      email_phone: "ईमेल या फोन नंबर",
      password: "पासवर्ड",
      role_tenant: "किरायेदार",
      role_owner: "मालिक",
      already_have_account: "पहले से ही एक अकाउंट है?",
      dont_have_account: "अकाउंट नहीं है?",
      verify_otp: "ओटीपी सत्यापित करें",
      otp_sent: "अपने डिवाइस पर भेजा गया कोड दर्ज करें",
      verify_btn: "सत्यापित करें और जारी रखें",
      dashboard: "डैशबोर्ड",
      browse_listings: "लिस्टिंग देखें",
      add_property: "संपत्ति जोड़ें",
      profile: "प्रोफ़ाइल",
      logout: "लॉगआउट",
    }
  },
  ta: {
    translation: {
      welcome: "Rentora-விற்கு வரவேற்கிறோம்",
      subtitle: "பிரீமியம் சொத்து வாடகை எளிதாக்கப்பட்டது.",
      login: "உள்நுழை",
      signup: "பதிவு செய்க",
      dashboard: "டாஷ்போர்டு",
      browse_listings: "பட்டியல்களைப் பார்க்க",
      add_property: "சொத்தைச் சேர்",
      profile: "சுயவிவரம்",
      logout: "வெளியேறு",
    }
  },
  te: {
    translation: {
      welcome: "Rentoraకు స్వాగతం",
      subtitle: "ప్రీమియం ఆస్తి అద్దెలు సులభతరం చేయబడ్డాయి.",
      login: "లాగిన్",
      signup: "సైన్ అప్",
      dashboard: "డ్యాష్‌బోర్డ్",
      browse_listings: "జాబితాలను బ్రౌజ్ చేయండి",
      add_property: "ఆస్తిని జోడించండి",
      profile: "ప్రొఫైల్",
      logout: "లాగ్ అవుట్",
    }
  },
  kn: {
    translation: {
      welcome: "Rentora ಗೆ ಸ್ವಾಗತ",
      subtitle: "ಪ್ರೀಮಿಯಂ ಆಸ್ತಿ ಬಾಡಿಗೆಗಳು ಸುಲಭವಾಗಿವೆ.",
      login: "ಲಾಗಿನ್",
      signup: "ಸೈನ್ ಅಪ್",
      dashboard: "ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
      browse_listings: "ಪಟ್ಟಿಗಳನ್ನು ವೀಕ್ಷಿಸಿ",
      add_property: "ಆಸ್ತಿಯನ್ನು ಸೇರಿಸಿ",
      profile: "ಪ್ರೊಫೈಲ್",
      logout: "ಲಾಗ್ ಔಟ್",
    }
  },
  ml: {
    translation: {
      welcome: "Rentora-യിലേക്ക് സ്വാഗതം",
      subtitle: "പ്രീമിയം പ്രോപ്പർട്ടി വാടകയ്‌ക്കെടുക്കൽ എളുപ്പമാക്കി.",
      login: "ലോഗിൻ",
      signup: "സൈൻ അപ്പ്",
      dashboard: "ഡാഷ്‌ബോർഡ്",
      browse_listings: "ലിസ്റ്റിംഗുകൾ ബ്രൗസ് ചെയ്യുക",
      add_property: "പ്രോപ്പർട്ടി ചേർക്കുക",
      profile: "പ്രൊഫൈൽ",
      logout: "ലോഗ് ഔട്ട്",
    }
  },
  mr: {
    translation: {
      welcome: "Rentora मध्ये आपले स्वागत आहे",
      subtitle: "प्रीमियम मालमत्ता भाड्याने देणे आता सोपे.",
      login: "लॉगिन",
      signup: "साइन अप",
      dashboard: "डॅशबोर्ड",
      browse_listings: "लिस्टिंग पहा",
      add_property: "मालमत्ता जोडा",
      profile: "प्रोफाइल",
      logout: "लॉगआउट",
    }
  },
  bn: {
    translation: {
      welcome: "Rentora-এ আপনাকে স্বাগতম",
      subtitle: "প্রিমিয়াম সম্পত্তি ভাড়া এখন সহজতর।",
      login: "লগইন",
      signup: "সাইন আপ",
      dashboard: "ড্যাশবোর্ড",
      browse_listings: "লিস্টিং দেখুন",
      add_property: "সম্পত্তি যোগ করুন",
      profile: "প্রোফাইল",
      logout: "লগআউট",
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: "en",
    fallbackLng: "en",
    interpolation: {
      escapeValue: false
    }
  });

export default i18n;
