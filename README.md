# Text-to-MongoDB Query Application

A comprehensive AI-powered application that converts plain English queries into MongoDB queries for a credit card acquisition system.

## 🎯 Overview

This project consists of two separate applications:

1. **UI Application** - Modern chat interface for natural language input
2. **Server Application** - Python-based backend that converts text to MongoDB queries using AI (OpenAI)

### Key Features

- 🤖 **AI-Powered Query Generation** - Uses OpenAI ChatCompletion API
- 🔒 **Privacy-First** - Only schema structures are sent to AI, never actual data
- 💬 **Chat Interface** - Beautiful, modern chat UI for seamless interaction
- ⚙️ **Configurable AI** - Support for OpenAI, Azure OpenAI, or any OpenAI-compatible API
- ⚡ **Real-time Execution** - Execute queries and see results instantly
- 📊 **Multiple Collections** - Works with customers, offers, applications, and campaigns

## 🚀 Getting Started

### 1. Setup Configuration
Copy the example environment file and set your configuration:
```bash
cp server/.env.example server/.env
```
**Required in `.env`**:
- `OPENAI_API_KEY`: Your API key
- `OPENAI_BASE_URL`: API endpoint (e.g., `https://api.openai.com/v1`)
- `OPENAI_MODEL`: Model name (e.g., `gpt-4o-mini`)
- `MONGO_URI`: MongoDB connection string
- `DB_NAME`: Database name

### 2. Start Application
Run the all-in-one startup script:
```bash
./start.sh
```
This script will:
- Check MongoDB status
- Setup virtual environment & dependencies
- Validate configuration
- Start both Server (port 5000) and UI (port 8000)

### 3. (Optional) Initialize Sample Data
If you want to test with sample notification data:
```bash
cd server
source venv/bin/activate
python init_sample_data.py
```
This creates 100 sample notifications across all channels.

## 🛠️ Management Scripts

- `./start.sh`: Starts both server and UI in the background
- `./stop.sh`: Stops all application processes and cleans up ports
- `./status.sh`: Checks if the server, UI, and MongoDB are running

## 💡 Example Queries

- **Simple**: "Show me all customers"
- **Filtered**: "Find customers with credit score above 700"
- **Aggregation**: "Show average credit score by employment status"
- **Aggregation**: "Count applications per card offer"
- **Advanced**: "Show me travel cards with signup bonus over 50000 points"

## 📋 Schema Configuration

The system uses a single `server/data/schemas/schemas.json` file that defines all MongoDB collections:

```json
{
  "description": "Multi-collection system description",
  "collections": {
    "collection_name": {
      "description": "Collection description",
      "fields": {
        "field_name": {
          "type": "string|integer|datetime|array|object",
          "description": "Field description",
          "indexed": true,
          "enum": ["value1", "value2"]
        }
      }
    }
  }
}
```

**At startup**, the server:
1. Loads `schemas.json`
2. Extracts all collections and their field definitions
3. Creates index information from `indexed` fields
4. Makes schemas available to the AI for query generation

**Note**: Only schema structures (field names, types, descriptions) are sent to AI - never actual data!

## 🏗️ Architecture & Privacy

- **Data Flow**: UI → API → OpenAI (Schemas only) → MongoDB → Results
- **Privacy**: **ACTUAL DATA NEVER GOES TO AI**. We only send the JSON schema (fields, types, and descriptions) so the AI knows how to write the query.

## 📄 License

This project is created for demonstration purposes.
