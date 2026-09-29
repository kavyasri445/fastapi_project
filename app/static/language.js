const supportedLanguages = ["en", "te", "hi", "ta"];

async function loadLanguage(language) {
    if (!supportedLanguages.includes(language)) {
        language = "en";
    }

    try {
        const response = await fetch(`/static/i18n/${language}.json`);

        if (!response.ok) {
            throw new Error(`Language file not found: ${language}`);
        }

        const translations = await response.json();

        document.querySelectorAll("[data-i18n]").forEach((element) => {
            const key = element.getAttribute("data-i18n");

            if (translations[key]) {
                element.textContent = translations[key];
            }
        });

        localStorage.setItem("selectedLanguage", language);

        const languageSelector = document.getElementById("languageSelector");

        if (languageSelector) {
            languageSelector.value = language;
        }

        document.documentElement.lang = language;

    } catch (error) {
        console.error("Language loading failed:", error);
    }
}


function initializeLanguageSelector() {
    const languageSelector = document.getElementById("languageSelector");

    if (!languageSelector) {
        return;
    }

    languageSelector.addEventListener("change", (event) => {
        loadLanguage(event.target.value);
    });

    const savedLanguage =
        localStorage.getItem("selectedLanguage") || "en";

    loadLanguage(savedLanguage);
}


document.addEventListener("DOMContentLoaded", () => {
    initializeLanguageSelector();
});