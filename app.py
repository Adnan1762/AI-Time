import streamlit as st
import requests
import json
import re
import time
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="AI Time Machine",
    page_icon="🕰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        background: ./time_bg.jpg;
        padding: 2rem 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }
    
    .timeline-item {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .timeline-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .news-item {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        border-left: 5px solid #ff6b6b;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease;
    }
    
    .news-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.15);
    }
    
    .chat-message {
        background: linear-gradient(135deg, #e3ffe7 0%, #d9e7ff 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #4ecdc4;
    }
    
    .mode-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .mode-card:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    .probability-high {
        background: linear-gradient(90deg, #ff6b6b, #ee5a24);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .probability-medium {
        background: linear-gradient(90deg, #feca57, #ff9ff3);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .probability-low {
        background: linear-gradient(90deg, #48dbfb, #0abde3);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .input-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .sidebar .stSelectbox {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 25px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .footer {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Check if google-generativeai is available
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    st.error("Please install google-generativeai: pip install google-generativeai")

# Configure Gemini API
GOOGLE_API_KEY = "your api key"

if GENAI_AVAILABLE:
    genai.configure(api_key=GOOGLE_API_KEY)

class TimeMachine:
    def __init__(self):
        if GENAI_AVAILABLE:
            # Try different model names that are available
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                try:
                    self.model = genai.GenerativeModel('gemini-1.5-pro')
                except:
                    try:
                        self.model = genai.GenerativeModel('models/gemini-1.5-flash')
                    except:
                        self.model = None
                        st.error("Could not initialize Gemini model. Please check your API key and model availability.")
        else:
            self.model = None
            
    def fetch_wikipedia_context(self, query):
        """Fetch relevant historical context from Wikipedia"""
        try:
            # Search for relevant articles
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
            
            # Extract key terms from query for better search
            search_terms = self.extract_search_terms(query)
            context_data = []
            
            for term in search_terms[:3]:  # Limit to 3 searches
                try:
                    response = requests.get(f"{search_url}{term}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        context_data.append({
                            'title': data.get('title', ''),
                            'extract': data.get('extract', ''),
                            'year': self.extract_year(data.get('extract', ''))
                        })
                except Exception as e:
                    continue
                    
            return context_data
        except Exception as e:
            st.error(f"Error fetching Wikipedia data: {str(e)}")
            return []
    
    def create_fallback_timeline(self, response_text, what_if_question):
        """Create a simple timeline if JSON parsing fails"""
        return {
            "timeline": [
                {"year": "Year 1", "event": "Initial change occurs", "impact": "The alternate timeline begins", "probability": "High"},
                {"year": "Year 5", "event": "First major consequences", "impact": "Society begins to adapt", "probability": "High"},
                {"year": "Year 10", "event": "Long-term effects emerge", "impact": "New patterns established", "probability": "Medium"},
                {"year": "Year 25", "event": "Generational changes", "impact": "New generation grows up in changed world", "probability": "Medium"},
                {"year": "Year 50", "event": "Historical legacy", "impact": "The change becomes part of history", "probability": "High"}
            ],
            "summary": f"This timeline explores the consequences of: {what_if_question}"
        }
    
    def extract_search_terms(self, query):
        """Extract key search terms from user query"""
        # Remove common words and extract meaningful terms
        stop_words = {'what', 'if', 'had', 'not', 'never', 'been', 'was', 'were', 'would', 'could', 'should'}
        words = re.findall(r'\b[A-Za-z]+\b', query.lower())
        
        # Keep important words and proper nouns
        meaningful_words = []
        for word in words:
            if word not in stop_words and len(word) > 2:
                meaningful_words.append(word.title())
        
        return meaningful_words[:5]  # Return top 5 terms
    
    def extract_year(self, text):
        """Extract year from text"""
        if not text:
            return None
        years = re.findall(r'\b(1[0-9]{3}|20[0-9]{2})\b', text)
        return int(years[0]) if years else None
    
    def generate_timeline(self, what_if_question, context_data):
        """Generate alternate history timeline"""
        if not self.model:
            return {
                "timeline": [{"year": "Error", "event": "Gemini API not available", "impact": "Please install google-generativeai", "probability": "Low"}],
                "summary": "API not configured"
            }
            
        context_text = "\n".join([f"- {item['title']}: {item['extract']}" for item in context_data])
        
        prompt = f"""
        You are an expert historian creating an alternate history timeline. Based on the following historical context and the hypothetical scenario, create a realistic alternate timeline.

        Historical Context:
        {context_text}

        Hypothetical Scenario: {what_if_question}

        Create a timeline of 7-10 major events that would likely occur as a result of this change. Format as JSON:
        {{
            "timeline": [
                {{
                    "year": "YYYY",
                    "event": "Brief description of major event",
                    "impact": "How this affects the broader world",
                    "probability": "High"
                }}
            ],
            "summary": "Brief overall summary of how the world would be different"
        }}

        Keep events realistic and grounded in historical cause-and-effect. Focus on major political, social, and technological changes.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    # If JSON parsing fails, create a simple timeline from the text
                    return self.create_fallback_timeline(response_text, what_if_question)
            else:
                # If no JSON found, create timeline from text
                return self.create_fallback_timeline(response_text, what_if_question)
        except Exception as e:
            st.error(f"Error generating timeline: {str(e)}")
            return {
                "timeline": [{"year": "Error", "event": "Failed to generate", "impact": str(e), "probability": "Low"}],
                "summary": "Generation failed"
            }
    
    def generate_newsfeed(self, what_if_question, context_data):
        """Generate newsfeed-style events"""
        if not self.model:
            return {"news_items": [{"headline": "API Error", "date": "Now", "source": "System", "summary": "Please install google-generativeai"}]}
            
        context_text = "\n".join([f"- {item['title']}: {item['extract']}" for item in context_data])
        
        prompt = f"""
        You are a news editor creating breaking news headlines for an alternate history scenario.

        Historical Context:
        {context_text}

        Alternate History Scenario: {what_if_question}

        Create 6-8 realistic news headlines that would appear in this alternate timeline. Format as JSON:
        {{
            "news_items": [
                {{
                    "headline": "Breaking news headline",
                    "date": "Month Year",
                    "source": "News organization name",
                    "summary": "Brief 2-3 sentence summary"
                }}
            ]
        }}

        Make headlines feel authentic and newsworthy. Include variety in dates and sources.
        """
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    return self.create_fallback_newsfeed(what_if_question)
            else:
                return self.create_fallback_newsfeed(what_if_question)
        except Exception as e:
            st.error(f"Error generating newsfeed: {str(e)}")
            return {"news_items": [{"headline": "Error", "date": "Now", "source": "System", "summary": str(e)}]}
    
    def create_fallback_newsfeed(self, what_if_question):
        """Create a simple newsfeed if JSON parsing fails"""
        return {
            "news_items": [
                {"headline": "Breaking: Historical Timeline Altered", "date": "Today", "source": "Time News", "summary": f"Major changes reported following: {what_if_question}"},
                {"headline": "Experts Analyze New Timeline", "date": "Yesterday", "source": "History Today", "summary": "Historians are working to understand the implications of the timeline change."},
                {"headline": "Society Adapts to New Reality", "date": "Last Week", "source": "World Report", "summary": "Citizens are adjusting to the altered course of history."}
            ]
        }
    
    def chat_with_historical_figure(self, figure_name, context, user_message):
        """Chat with a historical figure in the alternate timeline"""
        if not self.model:
            return "Sorry, Gemini API is not available. Please install google-generativeai."
            
        prompt = f"""
        You are {figure_name} in an alternate history where: {context}

        Respond to this message as {figure_name} would, considering how this alternate history would have affected their life, beliefs, and circumstances. Keep responses conversational and in character.

        Message: {user_message}

        Response as {figure_name}:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sorry, I'm having trouble responding right now. Error: {str(e)}"

def main():
    # Custom header
    st.markdown("""
    <div class="main-header">
        <h1>🕰️ AI Time Machine</h1>
        <p>Explore alternate histories with AI-powered timeline generation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if API is available
    if not GENAI_AVAILABLE:
        st.error("Please install the required dependency: `pip install google-generativeai`")
        st.stop()
    
    # Initialize the Time Machine
    if 'time_machine' not in st.session_state:
        st.session_state.time_machine = TimeMachine()
    
    # Enhanced Sidebar
    st.sidebar.markdown("## 🎛️ Control Panel")
    
    # Mode selection with descriptions
    mode_descriptions = {
        "Timeline Generator": "📅 Generate detailed alternate history timelines",
        "Newsfeed Simulation": "📰 See how events would unfold in news headlines",
        "Chat with Historical Figures": "💬 Talk to famous people from your alternate timeline"
    }
    
    mode = st.sidebar.selectbox(
        "Choose Mode:",
        list(mode_descriptions.keys()),
        format_func=lambda x: mode_descriptions[x]
    )
    
    # Add mode description
    st.sidebar.markdown(f"**Current Mode:** {mode_descriptions[mode]}")
    
    # Add some example questions
    st.sidebar.markdown("### 💡 Example Questions")
    example_questions = [
        "What if the Library of Alexandria never burned down?",
        "What if Napoleon won at Waterloo?",
        "What if the internet was invented in the 1800s?",
        "What if dinosaurs never went extinct?",
        "What if the Roman Empire never fell?"
    ]
    
    selected_example = st.sidebar.selectbox(
        "Try an example:",
        [""] + example_questions
    )
    
    # Main input with enhanced styling
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        what_if_question = st.text_input(
            "What if...",
            placeholder="e.g., What if the Library of Alexandria never burned down?",
            key="what_if_input",
            value=selected_example if selected_example else ""
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Add space
        generate_clicked = st.button("🚀 Generate", key="generate_btn")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Progress indicators
    if generate_clicked and what_if_question:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 Searching historical records...")
        progress_bar.progress(25)
        
        # Fetch context
        context_data = st.session_state.time_machine.fetch_wikipedia_context(what_if_question)
        
        status_text.text("🤖 Generating alternate timeline...")
        progress_bar.progress(50)
        
        # Store in session state
        st.session_state.current_question = what_if_question
        st.session_state.context_data = context_data
        
        if mode == "Timeline Generator":
            status_text.text("📅 Creating timeline events...")
            progress_bar.progress(75)
            timeline_data = st.session_state.time_machine.generate_timeline(what_if_question, context_data)
            st.session_state.timeline_data = timeline_data
            
        elif mode == "Newsfeed Simulation":
            status_text.text("📰 Generating news headlines...")
            progress_bar.progress(75)
            newsfeed_data = st.session_state.time_machine.generate_newsfeed(what_if_question, context_data)
            st.session_state.newsfeed_data = newsfeed_data
        
        status_text.text("✅ Complete!")
        progress_bar.progress(100)
        time.sleep(1)
        status_text.empty()
        progress_bar.empty()
    
    # Display results based on mode with enhanced styling
    if mode == "Timeline Generator" and 'timeline_data' in st.session_state:
        st.markdown("## 📅 Alternate Timeline")
        
        timeline = st.session_state.timeline_data
        
        # Display summary with styling
        st.markdown(f"""
        <div class="timeline-item">
            <h3>🎯 Timeline Summary</h3>
            <p><strong>{timeline.get('summary', 'No summary available')}</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Display timeline with enhanced styling
        for i, event in enumerate(timeline.get('timeline', [])):
            probability = event.get('probability', 'Medium')
            probability_class = f"probability-{probability.lower()}"
            
            st.markdown(f"""
            <div class="timeline-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; color: #667eea;">📍 {event.get('year', 'Unknown')}</h3>
                    <span class="{probability_class}">{probability} Probability</span>
                </div>
                <h4 style="margin: 0.5rem 0; color: #2c3e50;">{event.get('event', 'Unknown event')}</h4>
                <p style="margin: 0.5rem 0 0 0; color: #5a6c7d;"><strong>Impact:</strong> {event.get('impact', 'No impact specified')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif mode == "Newsfeed Simulation" and 'newsfeed_data' in st.session_state:
        st.markdown("## 📰 Alternate History News Feed")
        
        newsfeed = st.session_state.newsfeed_data
        
        for item in newsfeed.get('news_items', []):
            st.markdown(f"""
            <div class="news-item">
                <h3 style="margin: 0 0 0.5rem 0; color: #2c3e50;">📢 {item.get('headline', 'No headline')}</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="color: #667eea; font-weight: bold;">📅 {item.get('date', 'Unknown date')}</span>
                    <span style="color: #e74c3c; font-weight: bold;">📺 {item.get('source', 'Unknown')}</span>
                </div>
                <p style="margin: 0; color: black;">{item.get('summary', 'No summary available')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif mode == "Chat with Historical Figures":
        st.markdown("## 💬 Chat with Historical Figures")
        
        if 'current_question' not in st.session_state:
            st.info("🎯 Please generate an alternate history timeline first!")
        else:
            # Enhanced figure selection
            figures = {
                "Napoleon Bonaparte": "⚔️ Napoleon Bonaparte",
                "Albert Einstein": "🧠 Albert Einstein", 
                "Cleopatra": "👑 Cleopatra",
                "Leonardo da Vinci": "🎨 Leonardo da Vinci",
                "Marie Curie": "🔬 Marie Curie",
                "Winston Churchill": "🎩 Winston Churchill"
            }
            
            figure_name = st.selectbox(
                "Choose a historical figure:",
                list(figures.keys()),
                format_func=lambda x: figures[x],
                key="figure_select"
            )
            
            if 'chat_history' not in st.session_state:
                st.session_state.chat_history = []
            
            # Display chat history with styling
            st.markdown("### 💭 Conversation")
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message" style="margin-left: 2rem;">
                        <strong>🧑 You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message">
                        <strong>{figures[figure_name]} {figure_name}:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Chat input with enhanced styling
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_message = st.text_input("Your message:", key="chat_input", placeholder="Ask about their life in this alternate timeline...")
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                send_clicked = st.button("💬 Send", key="send_btn")
            
            if send_clicked and user_message:
                with st.spinner(f"💭 Waiting for {figure_name} to respond..."):
                    response = st.session_state.time_machine.chat_with_historical_figure(
                        figure_name, 
                        st.session_state.current_question, 
                        user_message
                    )
                    
                    # Add to chat history
                    st.session_state.chat_history.append({'role': 'user', 'content': user_message})
                    st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                    
                    st.rerun()
    
    # Enhanced Footer
    st.markdown("""
    <div class="footer">
        <p>🚀 <strong>Built with Streamlit and Google Gemini AI</strong></p>
        <p>✨ Explore infinite possibilities of history • Made with ❤️ for curious minds</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()