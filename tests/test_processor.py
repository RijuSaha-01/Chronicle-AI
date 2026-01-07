from chronicle_ai.processor import segment_diary_text

test_text_1 = """Morning: I woke up early and had coffee.
Afternoon: Had lunch with a friend.
Night: Watched a movie and slept."""

test_text_2 = """I woke up at 8am. It was a beautiful day.

Then I had some lunch and worked on my project.

Finally, I had dinner and went to bed."""

test_text_3 = """This is just some random text.
It has no markers.
It should be split into three parts if long enough."""

import json

def test():
    print("Test 1 (Markers):")
    print(json.dumps(segment_diary_text(test_text_1), indent=2))
    print("\nTest 2 (Hints):")
    print(json.dumps(segment_diary_text(test_text_2), indent=2))
    print("\nTest 3 (Fallback):")
    print(json.dumps(segment_diary_text(test_text_3), indent=2))

if __name__ == "__main__":
    test()
