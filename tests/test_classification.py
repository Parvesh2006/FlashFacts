from app.services.classification import KeywordDomainClassifier


def test_domain_classifier_ai():
    classifier = KeywordDomainClassifier()
    title = "OpenAI releases new GPT LLM neural network model"
    content = "The artificial intelligence breakthrough demonstrates deep learning capabilities."
    domain = classifier.classify(title, content)
    assert domain == "AI"


def test_domain_classifier_sports():
    classifier = KeywordDomainClassifier()
    title = "National team wins football championship match"
    content = "The tournament ended with a thrilling score in the stadium."
    domain = classifier.classify(title, content)
    assert domain == "Sports"


def test_domain_classifier_fallback():
    classifier = KeywordDomainClassifier()
    title = "Unrelated random text"
    content = "No specific domain keywords present here."
    domain = classifier.classify(title, content, default_domain="Economy")
    assert domain == "Economy"
