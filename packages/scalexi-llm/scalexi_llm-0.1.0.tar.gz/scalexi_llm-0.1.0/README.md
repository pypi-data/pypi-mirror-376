# **LLMProxy Documentation**

**Complete Guide**

## **Table of Contents**

* [Overview](https://www.google.com/search?q=%23-overview)  
* [Installation](https://www.google.com/search?q=%23-installation)  
* [Quick Start](https://www.google.com/search?q=%23-quick-start)  
* [ask\_llm Function](https://www.google.com/search?q=%23-ask_llm-function)  
* [Usage Examples](https://www.google.com/search?q=%23-usage-examples)  
* [Structured Outputs Schema Guidelines](https://www.google.com/search?q=%23-structured-output-schema-guidelines)  
* [Web Search Capability](https://www.google.com/search?q=%23-web-search-capability)  
* [Fallback Mechanisms](https://www.google.com/search?q=%23-fallback-mechanisms)  
* [Troubleshooting](https://www.google.com/search?q=%23-troubleshooting)  
* [Model Reference](https://www.google.com/search?q=%23-model-reference)

## **🎯 Overview**

llm.py is a comprehensive Python library that provides a unified interface for interacting with multiple Large Language Model (LLM) providers. It supports OpenAI, Anthropic, Google, Groq, DeepSeek, Alibaba, and Grok, with built-in fallbacks, structured output support, file processing, image analysis, and web search capabilities.

### **🚀 Core Features**

* Multi-provider support (7+ providers)  
* Structured output with Pydantic  
* File processing (PDF, DOCX, TXT, JSON)  
* Image analysis with vision fallback  
* Web search integration  
* Comprehensive fallback systems  
* Cost tracking and token usage  
* Robust error handling

### **🔧 Advanced Features**

* Structured output fallbacks  
* File content integration  
* Web search query generation  
* Granular fallback control  
* Provider-locked fallbacks  
* Cross-provider reliability

## **⚡ Installation**

\# Install dependencies  
pip install \-r requirements.txt

\# Required packages  
python-dotenv  
pathlib  
docx2txt  
pydantic  
openai  
xai-sdk  
google-genai  
groq  
anthropic  
python-docx  
pymupdf  
httpx

### **Environment Setup**

Create a .env file with your API keys:  
OPENAI\_API\_KEY=your\_openai\_key  
ANTHROPIC\_API\_KEY=your\_anthropic\_key  
GEMINI\_API\_KEY=your\_gemini\_key  
GROQ\_API\_KEY=your\_groq\_key  
DEEPSEEK\_API\_KEY=your\_deepseek\_key  
QWEN\_API\_KEY=your\_qwen\_key  
GROK\_API\_KEY=your\_grok\_key  
EXA\_API\_KEY=your\_exa\_key

## **🚀 Quick Start**

#### **Basic Setup**

from llm import LLMProxy

\# Initialize  
llm \= LLMProxy()

\# Basic usage  
response, execution\_time, token\_usage, cost \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    system\_prompt="You are a helpful assistant.",  
    user\_prompt="Explain quantum computing"  
)

print(f"Response: {response}")  
print(f"Cost: ${cost:.6f}")

#### **Return Values**

The function returns a tuple: (response, execution\_time, token\_usage, cost)

* **response**: The model's response (string or JSON)  
* **execution\_time**: Time taken in seconds (float)  
* **token\_usage**: Dictionary with token counts  
* **cost**: Total cost in USD (float)

#### **Token Usage Format**

{  
    "prompt\_tokens": 150,  
    "completion\_tokens": 200,  
    "total\_tokens": 350  
}

## **🔧 ask\_llm Function**

def ask\_llm(  
    model\_name="gpt-4o-mini",  
    system\_prompt="",  
    user\_prompt="",  
    temperature=None,  
    schema=None,  
    image\_path=None,  
    file\_path=None,  
    websearch=False,  
    retry\_limit=1,  
    fallback\_to\_provider\_best\_model=True,  
    fallback\_to\_standard\_model=True  
)

| Parameter | Type | Default | Description |
| :---- | :---- | :---- | :---- |
| **model\_name** | str | "gpt-4o-mini" | Model to use for generation |
| **system\_prompt** | str | "" | System prompt for the model |
| **user\_prompt** | str | "" | User prompt/message |
| **temperature** | float | None | Sampling temperature (0.0-2.0) |
| **schema** | Pydantic Model | None | Structured output schema |
| **image\_path** | str | None | Path to image file |
| **file\_path** | str | None | Path to file for analysis |
| **websearch** | bool | False | Enable web search |
| **retry\_limit** | int | 1 | Number of retry attempts |
| **fallback\_to\_provider\_best\_model** | bool | True | Enable fallback to best model from same provider |
| **fallback\_to\_standard\_model** | bool | True | Enable fallback to standard model (chatgpt-4o-latest) |
| **max\_tokens** | int | None | Maximum number of tokens to generate |

### **Return Values**

The function returns a tuple: (response, execution\_time, token\_usage, cost)

* **response**: The model's response (string or JSON)  
* **execution\_time**: Time taken in seconds (float)  
* **token\_usage**: Dictionary with token counts  
* **cost**: Total cost in USD (float)

### **Basic Usage**

response, execution\_time, token\_usage, cost \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    system\_prompt="You are a helpful assistant.",  
    user\_prompt="Explain quantum computing"  
)

### **Token Usage Format**

{  
    "prompt\_tokens": 150,  
    "completion\_tokens": 200,  
    "total\_tokens": 350  
}

The token usage dictionary provides detailed breakdown of token consumption across all API calls made during the request.

### **Best Models by Provider**

#### **Recommended Models**

* **OpenAI**: chatgpt-4o-latest  
* **Anthropic**: claude-sonnet-4-0  
* **Groq**: moonshotai/kimi-k2-instruct  
* **Google**: gemini-2.5-pro  
* **DeepSeek**: deepseek-reasoner  
* **Alibaba**: qwen-max-latest  
* **Grok**: grok-4-latest

## **💡 Usage Examples**

### **Basic Text Generation**

from llm import LLMProxy

llm \= LLMProxy()

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-sonnet-latest",  
    system\_prompt="You are a helpful assistant.",  
    user\_prompt="Explain machine learning in simple terms",  
    max\_tokens=500  
)

### **Structured Output**

from pydantic import BaseModel, Field  
from typing import List

class Recipe(BaseModel):  
    name: str \= Field(description="Recipe name")  
    ingredients: List\[str\] \= Field(description="Required ingredients")  
    steps: List\[str\] \= Field(description="Cooking steps")  
    cooking\_time: int \= Field(description="Cooking time in minutes")

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    user\_prompt="Create a recipe for chocolate chip cookies",  
    schema=Recipe,  
    max\_tokens=800  
)

### **Image Analysis**

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="gpt-4o",  
    user\_prompt="Analyze this image",  
    image\_path="photo.jpg",  
    max\_tokens=3500  
)

### **Combined Features**

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    system\_prompt="Analyze the provided content comprehensively",  
    user\_prompt="Analyze this resume and image",  
    file\_path="resume.pdf",  
    image\_path="profile.jpg",  
    websearch=True,  
    schema=AnalysisSchema  
)

## **📋 Structured Output Schema Guidelines**

### **⚠️ Critical Guidelines**

Adhere to these guidelines to ensure maximum compatibility across all LLM providers:

### **1\. Use Base Types with Descriptions**

#### **✅ Correct Approach**

class User(BaseModel):  
    email: str \= Field(description="User's email address")  
    created\_at: str \= Field(format="date-time")  
    age: int \= Field(description="User's age in years")

#### **❌ Incorrect Approach**

class User(BaseModel):  
    email: EmailStr  \# Too restrictive for LLMs  
    created\_at: datetime  \# Use str instead  
    age: PositiveInt  \# Use int with description

### **2\. Describe Constraints in Field Descriptions**

#### **✅ Correct Approach**

class Product(BaseModel):  
    price: float \= Field(description="Price must be greater than 0")  
    rating: int \= Field(description="Rating between 1-5 stars")  
    sku: str \= Field(description="Product SKU, 8-12 alphanumeric characters")

#### **❌ Incorrect Approach**

class Product(BaseModel):  
    price: float \= Field(..., gt=0)  \# Don't use constraint operators  
    rating: int \= Field(..., ge=1, le=5)  \# Use description instead  
    sku: str \= Field(..., regex=r'^\[A-Z0-9\]{8,12}$')  \# Describe in text

### **3\. Use Specific Models Instead of Dict\[str, Any\]**

#### **✅ Correct Approach**

class SensorReading(BaseModel):  
    sensor\_name: str  
    value: float  
    timestamp: str

class SensorData(BaseModel):  
device\_id: str  
readings: List\[SensorReading\]  
metadata: dict \= Field(description="Additional sensor metadata")  
\#\#\#\# ❌ Incorrect Approach

class SensorData(BaseModel):  
    device\_id: str  
    readings: Dict\[str, List\[Dict\[str, Any\]\]\]  \# Too generic  
    metadata: Dict\[str, Any\]  \# Lacks structure

### **4\. Avoid Self-Referential Types**

#### **✅ Correct Approach**

class Comment(BaseModel):  
    id: str  
    content: str  
    author: str  
    parent\_id: Optional\[str\] \= Field(description="Parent comment ID, null for top-level")  
    created\_at: str

#### **❌ Incorrect Approach**

class Comment(BaseModel):  
    id: str  
    content: str  
    replies: List\['Comment'\]  \# Avoid self-referential types  
    parent: Optional\[Comment\]  \# Use ID references instead

### **5\. Avoid Custom Validators**

#### **✅ Correct Approach**

class User(BaseModel):  
    username: str \= Field(description="Username must be 3-20 characters, alphanumeric only")  
    email: str \= Field(description="Valid email address format")  
    age: int \= Field(description="Age must be between 18-100")

#### **❌ Incorrect Approach**

class User(BaseModel):  
    username: str  
    email: str  
    age: int  
      
    @validator('username')  
    def validate\_username(cls, v):  
        if len(v) \< 3 or len(v) \> 20:  
            raise ValueError('Username must be 3-20 characters')  
        return v  
      
    @validator('email')  
    def validate\_email(cls, v):  
        if '@' not in v:  
            raise ValueError('Invalid email format')  
        return v

### **Complete Schema Examples**

#### **✅ User Profile Schema**

from pydantic import BaseModel, Field  
from typing import List, Optional

class Address(BaseModel):  
    street: str \= Field(description="Street address")  
    city: str \= Field(description="City name")  
    state: str \= Field(description="State abbreviation, 2 characters")  
    zip\_code: str \= Field(description="5-digit or 9-digit ZIP code")

class UserProfile(BaseModel):  
    user\_id: str \= Field(description="Unique user identifier")  
    username: str \= Field(description="Username, 3-20 characters, alphanumeric")  
    email: str \= Field(description="Valid email address")  
    age: int \= Field(description="Age in years, 18-100")  
    address: Address \= Field(description="User's physical address")  
    interests: List\[str\] \= Field(description="List of user interests")  
    is\_active: bool \= Field(description="Whether the user account is active")

#### **✅ Product Catalog Schema**

class Product(BaseModel):  
    product\_id: str \= Field(description="Unique product identifier")  
    name: str \= Field(description="Product name, 1-100 characters")  
    price: float \= Field(description="Product price in USD, greater than 0")  
    description: str \= Field(description="Product description, 10-500 characters")  
    category: str \= Field(description="Product category")  
    in\_stock: bool \= Field(description="Whether the product is in stock")  
    stock\_quantity: int \= Field(description="Number of items in stock, 0 or more")

class Order(BaseModel):  
    order\_id: str \= Field(description="Unique order identifier")  
    user\_id: str \= Field(description="ID of the user who placed the order")  
    products: List\[Product\] \= Field(description="List of products in the order")  
    total\_amount: float \= Field(description="Total order amount in USD")  
    order\_date: str \= Field(description="Order date in ISO format")  
    status: str \= Field(description="Order status: pending, processing, shipped, delivered")

### **Schema Validation Checklist**

#### **✅ Validation Checklist**

* All fields use basic Python types (str, int, float, bool, list)  
* All constraints are described in Field descriptions  
* No use of EmailStr, PositiveInt, or other specialized types  
* No custom validators (@validator)  
* No self-referential types  
* No Dict\[str, Any\] for structured data  
* All nested objects use specific Pydantic models  
* All descriptions are clear and comprehensive

### **Common Patterns**

#### **Optional Fields**

optional\_field: Optional\[str\] \= Field(description="Optional description")

#### **List Fields**

items: List\[str\] \= Field(description="List of string items")

#### **Union Types**

value: Union\[str, int\] \= Field(description="Value can be string or integer")

#### **Nested Models**

address: Address \= Field(description="User's address information")

#### **⚠️ Common Mistakes to Avoid**

* Using EmailStr instead of str with email description  
* Using datetime instead of str with format description  
* Using constr or conint instead of descriptions  
* Using Dict\[str, Any\] for structured data  
* Using @validator for simple constraints  
* Using List\['ModelName'\] for self-referential relationships

## **🔍 Web Search Capability**

The LLMProxy includes comprehensive web search functionality that automatically generates search queries and integrates results into your prompts. This feature provides real-time information retrieval to enhance your AI interactions.

### **Web Search Process**

#### **1\. Query Generation**

Uses a lightweight model from the same provider to intelligently generate search queries from your user prompt  
class QuerySchema(BaseModel):  
    query: str

#### **2\. Exa Search Integration**

Seamlessly integrates with Exa for comprehensive web search results  
EXA\_API\_KEY=your\_exa\_key

#### **3\. Seamless Integration**

Results are automatically formatted and integrated into your user prompt

### **Process Flow**

User Prompt  
    ↓  
Query Generation  
    ↓  
Exa Search  
    ↓  
Enhanced User Prompt with Search Results  
    ↓  
LLM Response Generation

#### **Automatic Schema Handling**

When web search is enabled without a specified schema, the system automatically uses SearchSchema:  
class SearchSchema(BaseModel):  
    result: str  
    sources: list\[str\]

This ensures structured output even when no custom schema is provided.

### **Integration Examples**

\# Research Agent  
response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-sonnet-latest",  
    system\_prompt="You are a research analyst. Provide comprehensive analysis with sources.",  
    user\_prompt="Analyze the impact of AI on healthcare in 2024",  
    websearch=True  
)

\# Fact-Checking Bot  
response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    system\_prompt="Verify the following claim with recent sources and provide evidence.",  
    user\_prompt="Is it true that quantum computers broke RSA encryption in 2024?",  
    websearch=True  
)

## **🔄 Fallback Mechanisms**

### **1\. Vision Fallback**

When a model doesn't support vision:

#### **Automatic Detection**

Checks model\_config\["vision"\] for vision support

#### **Generate Text Description**

Uses a vision-supporting model to generate image description

#### **Warning**

DeepSeek and Alibaba models fallback to Gemini for image description as they don't support vision.

#### **Seamless Integration**

Description added to user prompt automatically  
\# Non-vision model with image  
response \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  \# No vision support  
    image\_path="chart.png",         \# Will use fallback  
    user\_prompt="Analyze this chart"  
)

### **2\. Structured Output Fallbacks**

Three-tier fallback system with granular control:

#### **Tier 1: Native Structured Output**

Models with native schema support (OpenAI, Google)  
Direct schema validation

#### **Tier 2: Best Model Fallback (Provider-level)**

Uses best model from same provider  
Controlled by fallback\_to\_provider\_best\_model=True  
Example: claude-3-5-haiku → claude-sonnet-4-0

#### **Tier 3: Global Fallback (Cross-provider)**

Falls back to chatgpt-4o-latest  
Controlled by fallback\_to\_standard\_model=True  
Uses correct client and response function

### **Fallback Control Parameters**

#### **fallback\_to\_provider\_best\_model=True**

* **Purpose:** Control provider-level fallbacks  
* **Behavior:** When enabled, falls back to best model from same provider  
* **Example:** If claude-3-5-haiku fails, tries claude-sonnet-4-0  
* **Use Case:** Disable when you want strict model adherence

#### **fallback\_to\_standard\_model=True**

* **Purpose:** Control cross-provider fallbacks  
* **Behavior:** When enabled, falls back to chatgpt-4o-latest  
* **Example:** If claude-3-5-haiku fails, tries chatgpt-4o-latest  
* **Use Case:** Disable when you want to stay within provider ecosystem

### **Fallback Control Examples**

#### **Disable All Fallbacks**

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Analyze this",  
    schema=AnalysisSchema,  
    fallback\_to\_provider\_best\_model=False,  
    fallback\_to\_standard\_model=False  
)  
\# Only claude-3-5-haiku will be attempted, no fallbacks

#### **Provider-level Fallback Only**

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Analyze this",  
    fallback\_to\_provider\_best\_model=True,  
    fallback\_to\_standard\_model=False  
)  
\# Will try claude-sonnet-4-0 but NOT chatgpt-4o-latest

#### **Standard Model Fallback Only**

response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Analyze this",  
    fallback\_to\_provider\_best\_model=False,  
    fallback\_to\_standard\_model=True  
)  
\# Will try chatgpt-4o-latest directly, skipping provider best model

### **Fallback Decision Tree**

Original Model  
├── Success → Return response  
├── Failure → Check parameters  
    ├── fallback\_to\_provider\_best\_model=True  
    │   ├── Provider Best Model (e.g., claude-sonnet-4-0)  
    │   │   ├── Success → Return response  
    │   │   └── Failure → Check next fallback  
    │   └── fallback\_to\_standard\_model=True  
    │       └── chatgpt-4o-latest  
    │           ├── Success → Return response  
    │           └── Failure → Return error  
    └── fallback\_to\_provider\_best\_model=False  
        └── fallback\_to\_standard\_model=True  
            └── chatgpt-4o-latest  
                ├── Success → Return response  
                └── Failure → Return error

### **Advanced Fallback Scenarios**

#### **Strict Model Selection**

\# Only use specified model, no fallbacks  
response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Critical analysis",  
    fallback\_to\_provider\_best\_model=False,  
    fallback\_to\_standard\_model=False  
)

#### **Provider-locked Fallback**

\# Stay within Anthropic ecosystem  
response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Analysis",  
    fallback\_to\_provider\_best\_model=True,  
    fallback\_to\_standard\_model=False  
)

#### **Global Fallback Only**

\# Skip provider best model, go directly to standard  
response, \_, \_, \_ \= llm.ask\_llm(  
    model\_name="claude-3-5-haiku",  
    user\_prompt="Analysis",  
    fallback\_to\_provider\_best\_model=False,  
    fallback\_to\_standard\_model=True  
)

### **3\. Model Fallback Hierarchy**

Original Model  
├── Success → Return response  
├── Failure → Check parameters  
    ├── fallback\_to\_provider\_best\_model=True → Provider Best Model  
    └── fallback\_to\_standard\_model=True → chatgpt-4o-latest

### **4\. File Processing Fallbacks**

#### **Text-based PDFs**

PyMuPDF extraction in case pdf file upload isn't supported.

#### **Image-based PDFs**

Falls back to Gemini (gemini-2.5-flash-lite) for OCR extraction in case pdf file upload isn't supported.

#### **Other formats**

Format-specific processors

## **🔧 Troubleshooting**

### **Common Issues**

* **Model Not Found:** Check MODEL\_CONFIGS keys  
* **Vision Error:** Automatic fallback enabled  
* **Schema Validation:** Check schema structure  
* **API Errors:** Verify API keys in .env

### **Debug Mode**

import logging  
logging.basicConfig(level=logging.DEBUG)

### **Best Practices**

#### **Schema Design**

Use descriptive field names and comprehensive descriptions

#### **Error Handling**

Always check return values and handle None responses gracefully

#### **Cost Optimization**

Use appropriate models for tasks and monitor token usage

#### **Testing**

Test with various input types and verify fallback mechanisms

## **📋 Model Reference**

Complete reference of all supported models with their properties and configurations.

#### **⚡ Feature Support Legend**

**✅ \= Native Support | ⚡ \= Fallback Available**  
*All features work across all models through intelligent fallback mechanisms.*

* **Structured Outputs:** Fallback models generate JSON as string format that's automatically parsed.  
* **Image Input:** Fallback models receive automatic image descriptions added to prompts.

### **OpenAI Models**

#### **gpt-4o-mini**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 128,000 tokens  
* **Max Tokens:** 16,000  
* **Price:** $0.15 per 1M prompt, $0.60 per 1M completion

#### **gpt-5**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 256,000 tokens  
* **Max Tokens:** 128,000  
* **Reasoning Effort:** Medium  
* **Price:** $1.25 per 1M prompt, $10.00 per 1M completion

#### **gpt-4o**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 128,000 tokens  
* **Max Tokens:** 16,000  
* **Price:** $2.50 per 1M prompt, $10.00 per 1M completion

#### **gpt-4.1**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 32,000  
* **Price:** $2.00 per 1M prompt, $8.00 per 1M completion

#### **gpt-4.1-mini**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 32,000  
* **Price:** $0.40 per 1M prompt, $1.60 per 1M completion

#### **gpt-4.1-nano**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 32,000  
* **Price:** $0.10 per 1M prompt, $0.40 per 1M completion

#### **chatgpt-4o-latest**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 128,000 tokens  
* **Max Tokens:** 16,000  
* **Price:** $5.00 per 1M prompt, $15.00 per 1M completion

#### **o1**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 100,000  
* **Reasoning Effort:** High  
* **Price:** $15.00 per 1M prompt, $60.00 per 1M completion

#### **o3**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 100,000  
* **Reasoning Effort:** High  
* **Price:** $2.00 per 1M prompt, $8.00 per 1M completion

#### **o3-mini**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 100,000  
* **Reasoning Effort:** Medium  
* **Price:** $1.10 per 1M prompt, $4.40 per 1M completion

#### **o4-mini**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 100,000  
* **Reasoning Effort:** High  
* **Price:** $1.10 per 1M prompt, $4.40 per 1M completion

### **Anthropic Models**

#### **claude-sonnet-4-0**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 64,000  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **claude-sonnet-4-0-thinking**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 64,000  
* **Thinking Budget:** 4096 tokens  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **claude-3-7-sonnet-latest-thinking**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 64,000  
* **Thinking Budget:** 8000 tokens  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **claude-3-7-sonnet-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 64,000  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **claude-3-5-sonnet-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 8,192  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **claude-3-5-haiku-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 200,000 tokens  
* **Max Tokens:** 8,192  
* **Price:** $0.80 per 1M prompt, $4.00 per 1M completion

### **Google Models**

#### **gemini-2.0-flash**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 500,000 tokens  
* **Max Tokens:** 500,000  
* **Price:** $0.10 per 1M prompt (text/image/video), $0.70 per 1M audio, $0.40 per 1M completion

#### **gemini-2.5-flash**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 65,000  
* **Price:** $0.30 per 1M prompt (text/image/video), $2.50 per 1M audio, $0.60 per 1M completion

#### **gemini-2.5-pro**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 65,000  
* **Price:** $1.25 per 1M prompt (text/image/video), $10.00 per 1M completion

#### **gemini-2.5-flash-lite**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 65,536  
* **Price:** $0.10 per 1M prompt (text/image/video), $0.40 per 1M completion

#### **gemini-1.5-pro**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 1,000,000  
* **Price:** $1.25 per 1M prompt, $5.00 per 1M completion

#### **gemini-1.5-flash**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 500,000 tokens  
* **Max Tokens:** 8,192  
* **Price:** $0.075 per 1M prompt, $0.30 per 1M completion

#### **gemini-1.5-flash-8b**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ✅ Yes  
* **Context Length:** 500,000 tokens  
* **Max Tokens:** 8,192  
* **Price:** $0.0375 per 1M prompt, $0.15 per 1M completion

### **Groq Models**

#### **llama-3.1-8b-instant**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,000 tokens  
* **Max Tokens:** 131,000  
* **Price:** $0.05 per 1M prompt, $0.08 per 1M completion

#### **llama-3.3-70b-versatile**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,000 tokens  
* **Max Tokens:** 32,000  
* **Price:** $0.59 per 1M prompt, $0.79 per 1M completion

#### **deepseek-r1-distill-llama-70b**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 16,000 tokens  
* **Max Tokens:** 16,000  
* **Price:** $0.75 per 1M prompt, $0.99 per 1M completion

#### **moonshotai/kimi-k2-instruct**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 16,384  
* **Price:** $1.00 per 1M prompt, $3.00 per 1M completion

#### **openai/gpt-oss-120b**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 65,526  
* **Price:** $0.15 per 1M prompt, $0.75 per 1M completion

#### **openai/gpt-oss-20b**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 65,526  
* **Price:** $0.10 per 1M prompt, $0.50 per 1M completion

#### **meta-llama/llama-4-scout-17b-16e-instruct**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 8,192  
* **Price:** $0.11 per 1M prompt, $0.34 per 1M completion

#### **meta-llama/llama-4-maverick-17b-128e-instruct**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 8,192  
* **Price:** $0.20 per 1M prompt, $0.60 per 1M completion

### **DeepSeek Models**

#### **deepseek-chat**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 64,000 tokens  
* **Max Tokens:** 8,096  
* **Prompt Limit:** 70,000  
* **Price:** $0.07 per 1M prompt, $0.27 per 1M completion

#### **deepseek-reasoner**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 64,000 tokens  
* **Max Tokens:** 8,096  
* **Prompt Limit:** 70,000  
* **Price:** $0.14 per 1M prompt, $2.19 per 1M completion

### **Alibaba Models**

#### **qwen-max-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 30,720 tokens  
* **Max Tokens:** 8,192  
* **Price:** $1.60 per 1M prompt, $6.40 per 1M completion

#### **qwen-turbo-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 16,384  
* **Price:** $0.05 per 1M prompt, $0.20 per 1M completion

#### **qwen-plus-latest**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 995,904 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.40 per 1M prompt, $1.20 per 1M completion

#### **qwen-flash**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 1,000,000 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.05 per 1M prompt, $0.40 per 1M completion

#### **qwen3-235b-a22b-thinking-2507**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 126,976 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.70 per 1M prompt, $8.40 per 1M completion

#### **qwen3-235b-a22b-instruct-2507**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 129,024 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.70 per 1M prompt, $2.80 per 1M completion

#### **qwen3-30b-a3b-thinking-2507**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 126,976 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.20 per 1M prompt, $2.40 per 1M completion

#### **qwen3-30b-a3b-instruct-2507**

* **Structured Output:** ⚡ Fallback  
* **Vision:** ⚡ Fallback  
* **Context Length:** 126,976 tokens  
* **Max Tokens:** 32,768  
* **Price:** $0.20 per 1M prompt, $0.80 per 1M completion

### **Grok Models**

#### **grok-3-mini-latest**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 131,072  
* **Price:** $0.30 per 1M prompt, $0.50 per 1M completion

#### **grok-3-latest**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 131,072  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

#### **grok-3-mini-fast-latest**

* **Structured Output:** ✅ Yes  
* **Vision:** ⚡ Fallback  
* **Context Length:** 131,072 tokens  
* **Max Tokens:** 131,072  
* **Price:** $0.60 per 1M prompt, $4.00 per 1M completion

#### **grok-4-latest**

* **Structured Output:** ✅ Yes  
* **Vision:** ✅ Yes  
* **Context Length:** 256,000 tokens  
* **Max Tokens:** 256,000  
* **Price:** $3.00 per 1M prompt, $15.00 per 1M completion

## **🚀 Ready to Use**

LLMProxy is fully documented and ready for action. Explore the infinite possibilities of AI integration with this comprehensive toolkit.  
\# Quick Start  
llm \= LLMProxy()  
response, execution\_time, token\_usage, cost \= llm.ask\_llm(  
    model\_name="chatgpt-4o-latest",  
    user\_prompt="Hello, AI world\!"  
)  
print(f"Response: {response}")  
print(f"Cost: ${cost:.6f}")  
