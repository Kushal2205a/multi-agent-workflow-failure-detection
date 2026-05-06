from monitor import similarity

# paste the full reviewer message 1 between the triple quotes
text1 = """
As a senior reviewer, I cannot let this pass as production-ready...
""".lower()

# paste the full reviewer message 2 between the triple quotes  
text2 = """
While this is significantly more robust, production-ready is a moving target...
""".lower()

keywords = ["reject", "missing", "incorrect", "fix", "not complete"]

print("Turn 2 matches:", [k for k in keywords if k in text1])
print("Turn 4 matches:", [k for k in keywords if k in text2])
print("Similarity:", round(similarity(text1, text2), 3))