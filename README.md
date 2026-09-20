# Travel Planning Assistant (RAG + MCP)

## Technologies Used

- Python 3.13
- ChromaDB (vector store)
- sentence-transformers/all-MiniLM-L6-v2 (Embeddings model)
- gemini-3.5-flash-lite (LLM model)
- LangChain
- FastMCP

## Project Architecture

- app.py
  - Streamlit chat UI
  - Connects RAG + MCP tools with LangGraph ReAct agent
  - Keeps multi-turn conversation context

- ingest.py
  - Loads markdown travel documents from data folder
  - Splits documents into chunks
  - Creates embeddings (all-MiniLM-L6-v2)
  - Stores vectors in Chroma (chroma_db/) folder

- weather_server.py
  - MCP weather server using FastMCP
  - Tool 1: get_weather() for current weather
  - Tool 2: get_weather_forecast() for forecast

- currency_server.py
  - MCP currency server using FastMCP
  - Tool: convert_currency()

- rag.py
  - CLI version of the assistant

## Knowledge Base Sources

Copied the content from the web sites around areaes which are metioned in assignment and created the .md files in data folder

1. Wikivoyage Singapore Travel Guide
	- https://en.wikivoyage.org/wiki/Singapore

2. Visit Singapore - Essential Travel Information
	- https://www.visitsingapore.com/travel-tips/essential-travel-information/

3. Visit Singapore - Sample Itineraries
	- https://www.visitsingapore.com/singapore-itineraries/

4. Visit Singapore - Things to Do
	- https://www.visitsingapore.com/see-do-singapore/

## RAG Workflow

1. Load markdown documents from data/
2. Split into meaningful chunks (chunk_size=800, overlap=100)
3. Create embeddings using sentence-transformers/all-MiniLM-L6-v2
4. Store chunks + embeddings in Chroma vector DB
5. Retrieve top relevant chunks for each question
6. Use retrieved chunks to answer
7. Show source title and source URL in generated answers

## MCP Tools

### Weather MCP

- Current weather by city
- Forecast for next N days (default 3)

### Currency MCP

- Currency conversion between two currencies

## Prompt

Prompt design in app.py and rag.py follows these points:

- Destination facts should come from RAG tool
- Current weather/currency should come from MCP tools
- If weather/currency is asked, MCP must be used before final answer
- If MCP is unavailable, clearly mention current data could not be fetched
- Do not invent facts/URLs
- If KB does not have enough info, explicitly say so
- Keep output structured and include source references

system_prompt = (
            "You are an expert Travel Planning Assistant. "
            "Use the search_knowledge_base tool for destination facts, attractions, culture, transport, and itineraries. "
            "Use the MCP tools for real-time information like current weather conditions and currency conversions. "
            "If the user asks about weather or currency, must call an MCP tool before answering. "
            "If MCP tools are unavailable or fail, clearly say that current data could not be fetched. "
            "If the knowledge base does not have enough detail, clearly state that and do not invent facts. "
            "Guidelines for Output: "
            "1. Synthesize the information smoothly. Clean up any raw markdown headers, tags, or structural text artifacts retrieved from the source documents. "
            "2. Present your answers using clean, professional Markdown formatting (bullet points, bold text, and clear section dividers). "
            "3. Ensure strict text spacing: Never let words, numbers, punctuation, or brackets collide (e.g., always leave spaces around numbers, prices, and parentheses like '$34 respectively'). "
            "4. Always cite your sources clearly at the end or within the response when referencing knowledge-base content. "
            "5. Do not invent facts, numbers, or URLs that are not in tool results or retrieved content."
        )

## Setup Instructions

### Install

1. Create and activate virtual env
2. Install dependencies:

	pip install -r requirements.txt

3. Create .env file with:

	GEMINI_API_KEY=your_key_here

### Build the vector DB

Run:

python ingest.py

## Run the Application

### Streamlit UI

streamlit run app.py

### CLI version

python rag.py

Type exit to close CLI session.

## Sample questions and response

Q - `I have INR 60000 budget, convert to SGD and suggest three-day itinerary.`

Response - 

Based on the current exchange rate, your budget of INR 60000 converts to approximately SGD 799.80. This provides a comfortable budget for a 3 - day trip when balancing ticketed attractions with street food and public transit.

Here is a 3 - day suggested itinerary covering Singapore's iconic landmarks and cultural neighborhoods:

Day 1 : Iconic Architecture & Marina Bay
Morning : Start with a visit to The Merlion for classic photographs overlooking the waterfront, then stroll around Marina Bay.
Afternoon : Explore the modern architecture and high - end shopping around Marina Bay Sands.
Evening : Walk over to Gardens by the Bay to experience the futuristic Supertree Groves and light shows.

Day 2 : Rich Culture & Heritage Neighborhoods
Morning : Head to Little India to explore vibrant streets, colorful storefronts, historic temples, and fragrant flower garlands.
Afternoon : Walk through Kampong Gelam to see the striking mosque, trendy cafes, and rich local heritage.
Evening : Visit Chinatown to explore historic temples, traditional local shops, and enjoy authentic local dishes for dinner.

Day 3 : Civic District & City in Nature
Morning : Explore the historic heritage buildings and museums in the Civic District.
Afternoon : Take a relaxing trip to the Singapore Botanic Gardens and the National Orchid Garden, a UNESCO World Heritage site showcasing tropical flora.
Evening : Spend your final evening shopping or enjoying local cuisine in one of Singapore's vibrant neighborhoods like Katong - Joo Chiat.

Sources: Visit Singapore ( https://www.visitsingapore.com/see-do-singapore/ and https://www.visitsingapore.com/singapore-itineraries/ )

Q - `adjust the activities based on the weather forecast for all 3 days`

Response - 

Here is the weather forecast for your 3 - day trip to Singapore:

Day 1 (Sep 20) : High of 31.1 °C, low of 26.2 °C with expected thunderstorms / higher precipitation (10.8 mm).
Day 2 (Sep 21) : High of 31.0 °C, low of 26.2 °C with light drizzle / moderate rain chances (2.4 mm).
Day 3 (Sep 22) : High of 31.8 °C, low of 26.2 °C with light rain showers (2.0 mm).
Because Singapore's tropical climate brings a strong chance of rain and thunderstorms (especially on Day 1), your itinerary has been adjusted to feature more indoor and covered activities during wet weather windows, while keeping your vegetarian dining stops intact:

Day 1 : Marina Bay & High Indoor Shelter (Thunderstorm Forecast)
Morning : Start indoors early at The Shoppes at Marina Bay Sands and explore the high - end shopping malls to stay completely dry if morning storms roll in.
Mid - Day (Vegetarian Lunch) : Enjoy a sit - down vegetarian lunch at a mall food hall or restaurant near Marina Bay Sands.
Afternoon : Visit the indoor, air - conditioned Flower Dome and Cloud Forest cooled conservatories at Gardens by the Bay. This lets you enjoy the lush plants and waterfalls completely sheltered from any afternoon downpours.
Evening : Walk over to see The Merlion if the weather clears up, or enjoy dinner at Jurassic Nest Food Hall or Satay by the Bay which offer covered dining areas.

Day 2 : Heritage Neighborhoods & Covered Walkways (Light Rain)
Morning : Explore Little India. Bring an umbrella for brief outdoor walks, ducking quickly into historic temples or vibrant indoor shops when the light drizzle picks up.
Mid - Day (Vegetarian Lunch) : Warm up with a traditional South Indian vegetarian thali or dosas at a classic indoor restaurant like Komala Vilas.
Afternoon : Head over to Kampong Gelam. Explore the indoor boutique cafes, spice shops, and covered walkways around the heritage district to stay dry.
Evening : Conclude your evening in Chinatown, browsing the indoor heritage centers, covered market stalls, and enjoying a comforting vegetarian dinner.

Day 3 : Civic District & Culture (Showers Clearing)
Morning (Flexible Nature / Indoor Shift) : Since light rain is expected, swap the open - air Botanic Gardens for the world - class museums and galleries in the Civic District to stay completely dry during the morning hours.
Mid - Day (Vegetarian Lunch) : Enjoy a relaxed vegetarian meal inside a cafe or restaurant at the National Gallery Singapore or nearby Raffles City.
Afternoon : If the weather clears up for a brief shower break, head out to take a quick stroll through the Singapore Botanic Gardens, or stick to covered heritage walks.
Evening : Wrap up your trip exploring the colorful indoor shophouse boutiques and enjoying a warm bowl of vegetarian laksa in Katong - Joo Chiat.

Sources: Visit Singapore ( https://www.visitsingapore.com/see-do-singapore/ )

Q - `What are the must-visit attractions in Singapore?`

Response - 

Singapore offers a vibrant mix of iconic modern architecture, rich cultural neighborhoods, and lush green spaces. Here are the must-visit attractions categorized by what they have to offer:

Iconic Architecture & Landmarks
Marina Bay Sands & Marina Bay: World - famous landmarks offering incredible skyline views, high - end shopping, and entertainment.
Gardens by the Bay: A stunning futuristic park featuring the famous Supertree Groves and cooled conservatories.
The Merlion: Singapore's national personification and a must - visit photo spot overlooking the waterfront.
Civic District: Home to historic heritage buildings, museums, and significant monuments.

Culture & Heritage Neighborhoods
Chinatown: Explore historic temples, traditional local shops, and authentic street food.
Little India: Experience vibrant streets filled with colorful storefronts, fragrant flower garlands, and historic temples.
Kampong Gelam: A historic district known for its striking mosque, trendy cafes, and rich Malay - Arab heritage.
Katong - Joo Chiat: Famous for its well - preserved Peranakan shophouses and traditional local cuisine.

City in Nature
Singapore Botanic Gardens & National Orchid Garden: A UNESCO World Heritage site showcasing a breathtaking variety of tropical flora and orchids.
Nature Reserves & Parks: Perfect for outdoor enthusiasts looking to experience Singapore's lush tropical greenery and scenic walking trails.

Source: Visit Singapore ( https://www.visitsingapore.com/see-do-singapore/ )

Q- `what about the smoking rules?`

Response - 
Singapore has very strict laws regarding smoking, and regulations are heavily enforced. Here is what you need to know:

Where Smoking is Prohibited: Smoking is strictly forbidden in almost all indoor spaces and public areas. This includes buildings, retail shops, food establishments (including hawker centres and restaurants), public transport nodes, public service vehicles, and sports facilities.
Designated Smoking Areas: You can only smoke in clearly marked designated smoking areas, which are usually outfitted with yellow boxes or signs indicating that smoking is permitted.
Fines: Violating smoking regulations can result in heavy fines.

Source: Visit Singapore ( https://www.visitsingapore.com/travel-tips/essential-travel-information/ )



### More Question which I asked - 

- How can a tourist travel around Singapore?
- What is the weather in Singapore today?
- Convert INR 50000 to SGD.