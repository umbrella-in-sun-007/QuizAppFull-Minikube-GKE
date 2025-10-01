# Quick Start Guide - Create Your First Quiz

## Step 1: Access Wagtail Admin
1. Open browser: `http://localhost:8000/admin/`
2. Login with your superuser credentials

## Step 2: Create a Quiz Page
1. Click **Pages** in the left sidebar
2. Click on **Home** (the root page)
3. Click the **"..."** menu → **Add child page**
4. Select **Quiz** from the list

## Step 3: Configure Quiz Settings
Fill in the following fields:

### Basic Info
- **Title**: "Python Basics Quiz" (example)
- **Description**: "Test your knowledge of Python fundamentals"

### Quiz Settings
- **Duration (minutes)**: 30
- **Pass percentage**: 70
- **Max attempts**: 3

### Display Options
- **Is active**: ✓ (checked)
- **Show results immediately**: ✓ (checked)
- **Randomize questions**: (optional)

### Schedule (optional)
- Leave blank for always available
- Or set Start/End dates

## Step 4: Add Questions

### Question 1 (Single Choice)
1. Scroll to **Questions** section
2. Click **Add question**
3. **Question text**: "What is the output of print(2 + 2)?"
4. **Question type**: Single Choice
5. **Marks**: 1
6. **Is required**: ✓

Add Options:
- Click **Add answer option**
  - **Option text**: "4"
  - **Is correct**: ✓ (checked)
- Click **Add answer option**
  - **Option text**: "22"
  - **Is correct**: (unchecked)
- Click **Add answer option**
  - **Option text**: "Error"
  - **Is correct**: (unchecked)

**Explanation**: "In Python, the + operator performs addition for numbers, so 2 + 2 equals 4."

### Question 2 (Multiple Choice)
1. Click **Add question**
2. **Question text**: "Which of the following are valid Python data types?"
3. **Question type**: Multiple Choice
4. **Marks**: 2

Add Options:
- **Option text**: "int" - **Is correct**: ✓
- **Option text**: "float" - **Is correct**: ✓
- **Option text**: "number" - **Is correct**: ✗
- **Option text**: "string" - **Is correct**: ✓

**Explanation**: "Python has int, float, and str (string) as basic data types. 'number' is not a Python data type."

### Question 3 (True/False)
1. Click **Add question**
2. **Question text**: "Python is case-sensitive"
3. **Question type**: True/False
4. **Marks**: 1

Add Options:
- **Option text**: "True" - **Is correct**: ✓
- **Option text**: "False" - **Is correct**: ✗

**Explanation**: "Python IS case-sensitive. Variable names like 'name' and 'Name' are different."

### Question 4 (Short Answer)
1. Click **Add question**
2. **Question text**: "What does PEP stand for in Python?"
3. **Question type**: Short Answer
4. **Marks**: 1

**Explanation**: "PEP stands for Python Enhancement Proposal. It's a design document providing information to the Python community."

## Step 5: Publish Quiz
1. Scroll to bottom of page
2. Click **Publish** button (green)
3. Your quiz is now live!

## Step 6: Test Your Quiz

### As Student:
1. Logout from admin (or open incognito window)
2. Go to: `http://localhost:8000/quiz/login/`
3. Create/use a student account
4. Login and see your quiz in the list
5. Click **Start Quiz**
6. Complete and submit
7. View results

### As Teacher:
1. Go to: `http://localhost:8000/quiz/{quiz-id}/analytics/`
   (Replace {quiz-id} with actual ID from URL)
2. View comprehensive statistics

## Tips for Your First Quiz

✓ **Start Small**: Create 5-10 questions first
✓ **Test Yourself**: Take the quiz to ensure it works
✓ **Add Explanations**: Helps students learn from mistakes
✓ **Set Reasonable Time**: Allow 1-2 minutes per question
✓ **Multiple Attempts**: Enable for learning purposes

## Common Issues

### Quiz Not Showing?
- Check **Is active** is checked
- Check Start/End dates (if set)
- Make sure quiz is Published, not Draft

### Timer Not Working?
- Check browser JavaScript is enabled
- Refresh the page

### Can't See Analytics?
- Make sure you're logged in as staff/admin
- Use direct URL: `/quiz/{id}/analytics/`

## Next Steps

1. Create more quizzes for different topics
2. Invite students to register
3. Monitor student performance via analytics
4. Add more question types
5. Set up automated schedules for assessments

## Getting Help

Check the main README_QUIZ_APP.md for detailed documentation.

Happy Quiz Creating! 🎓
