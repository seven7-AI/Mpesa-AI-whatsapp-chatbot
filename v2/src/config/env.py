import os
from dotenv import load_dotenv

load_dotenv()


#####################################
# STORAGE
#####################################

# neo4j
NEO4J_URI=os.getenv("NEO4J_URI")
NEO4J_USERNAME=os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")

####################################
# DARAJA
###################################

# local
MPESA_CONSUMER_KEY=os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET=os.getenv("MPESA_SECRET_KEY")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY") # From Mpesa portal
MPESA_CALLBACK_URL = "http://yourcustomurl.local/"
TILL_SHORTCODE=os.getenv("TILL_SHORTCODE") 
MPESA_INITIATOR_USERNAME=os.getenv("MPESA_INITIATOR_USERNAM")
MPESA_SECURITY_CREDENTIAL=os.getenv("MPESA_SECURITY_CREDENTIAL")






######################################
# lLM
#####################################

# LLM PROVIDERS
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY=os.getenv("ANTHROPIC_API_KEY")



######################################
# PLATFORMS 
######################################

# WHATSAPP_BOT
WHATSAPP_ACCESS_TOKEN=os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_APP_ID=os.getenv("WHATSAPP_APP_ID")
WHATSAPP_APP_SECRET=os.getenv("WHATSAPP_APP_SECRET")
VERSION='v18.0'
WHATSAPP_PHONE_NUMBER_ID=os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFICATION_TOKEN=os.getenv("WHATSAPP_VERIFICATION_TOKEN")


# TELEGRAM_BOT
TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")


######################################
# VOICE AND VISUAL
######################################
# ELEVENLABS
ELEVENLABS_API_KEY=os.getenv("ELEVENLABS_API_KEY")

# # DEEPGRAM
# DEEPGRAM_API_KEY=

# #########################################
# # LANCHAIN
# #########################################   

# LANCHAIN_API_KEY=





# #########################################
# # BIGTOOLS API KEYS
# #########################################

# GOOGLE_API_KEY=






