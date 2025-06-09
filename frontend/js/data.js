export const appData = {
  "tracks": [
    {
      "id": 1,
      "title": "JavaScript Fundamentals",
      "description": "Master the basics of JavaScript programming",
      "progress": 65,
      "modules": 12,
      "difficulty": "Beginner",
      "tags": ["Programming", "Web Development"],
      "modules_list": [
        {"id": 1, "title": "Variables and Types", "completed": true, "progress": 100},
        {"id": 2, "title": "Functions and Scope", "completed": true, "progress": 100},
        {"id": 3, "title": "Objects and Arrays", "completed": false, "progress": 30},
        {"id": 4, "title": "DOM Manipulation", "completed": false, "progress": 0}
      ]
    },
    {
      "id": 2,
      "title": "Python Data Science",
      "description": "Analyze data with Python and pandas",
      "progress": 40,
      "modules": 15,
      "difficulty": "Intermediate",
      "tags": ["Python", "Data Science"],
      "modules_list": [
        {"id": 1, "title": "NumPy Basics", "completed": true, "progress": 100},
        {"id": 2, "title": "Pandas DataFrames", "completed": false, "progress": 60},
        {"id": 3, "title": "Data Visualization", "completed": false, "progress": 0}
      ]
    },
    {
      "id": 3,
      "title": "Machine Learning Basics",
      "description": "Introduction to ML algorithms and concepts",
      "progress": 0,
      "modules": 20,
      "difficulty": "Advanced",
      "tags": ["AI", "Machine Learning"],
      "modules_list": [
        {"id": 1, "title": "Linear Regression", "completed": false, "progress": 0},
        {"id": 2, "title": "Classification", "completed": false, "progress": 0},
        {"id": 3, "title": "Neural Networks", "completed": false, "progress": 0}
      ]
    },
    {
      "id": 4,
      "title": "React Development",
      "description": "Build modern web applications with React",
      "progress": 80,
      "modules": 10,
      "difficulty": "Intermediate",
      "tags": ["React", "Frontend"],
      "modules_list": [
        {"id": 1, "title": "Components and JSX", "completed": true, "progress": 100},
        {"id": 2, "title": "State and Props", "completed": true, "progress": 100},
        {"id": 3, "title": "Hooks", "completed": false, "progress": 50}
      ]
    }
  ],
  "current_lesson": {
    "title": "Understanding JavaScript Objects",
    "content": "Objects are fundamental data structures in JavaScript that allow you to store collections of key-value pairs. They provide a way to group related data and functionality together.",
    "code_example": "const user = {\n  name: 'John Doe',\n  age: 30,\n  email: 'john@example.com',\n  greet() {\n    return `Hello, I'm ${this.name}`;\n  }\n};",
    "practice_task": "Create an object representing a book with properties: title, author, pages, and a method to get book info."
  },
  "chat_messages": [
    {"id": 1, "sender": "ai", "message": "Привет! Я ваш AI-наставник. Готовы изучать JavaScript объекты?", "timestamp": "10:30"},
    {"id": 2, "sender": "user", "message": "Да, давайте начнем!", "timestamp": "10:31"},
    {"id": 3, "sender": "ai", "message": "Отлично! Объекты в JavaScript - это основа для понимания современного программирования. Начнем с простого примера.", "timestamp": "10:31"}
  ],
  "practice_modes": [
    {
      "id": "task",
      "title": "Practice Task",
      "description": "Самостоятельное задание для закрепления материала",
      "icon": "📝"
    },
    {
      "id": "recall",
      "title": "Recall Loop",
      "description": "Повторение через систему интервальных повторений",
      "icon": "🔄"
    },
    {
      "id": "simulation",
      "title": "Simulation",
      "description": "Интерактивная практика в реальных сценариях",
      "icon": "🎮"
    }
  ]
}; 