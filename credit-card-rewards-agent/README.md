(base) PS C:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent> (Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned) ; (& "c:\IITM AGENTIC AI WORKFLOW\CAPSTON PROJECT\credit-card-rewards-agent\.venv\Scripts\Activate.ps1")
\CAPSTON PROJECT\credit-card-rewards-agent> pip install -r requirements.txt                                                                                                                      
\CAPSTON PROJECT\credit-card-rewards-agent> python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY')[-8:])"                                        
KxvBSJIA              
\CAPSTON PROJECT\credit-card-rewards-agent> python -c "from dotenv import load_dotenv; load_dotenv(); import os; from openai import OpenAI; client=OpenAI(api_key=os.getenv('OPENAI_API_KEY')); print(client.models.list())"

\CAPSTON PROJECT\credit-card-rewards-agent> streamlit run app\streamlit_app.py                                