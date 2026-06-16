############################################################################## 
#                           Streamlit Overview                               #
#   Last modified 3/16/2026                                                  #
#                                                                            #     
#   To execute, type the following into the terminal:                        #                                        
#    streamlit run "D:\Work_Delaney\Streamlit\Overview.py"                   # 
#                                                                            # 
#   This is the app's landing page. It includes information on the project,  # 
#   the links to the Github page with our finished work and our two papers,  #
#   and a description of each dashboard.                                     # 
#                                                                            #  
##############################################################################

import streamlit as st


###############################
# Main Page Text              #
###############################

st.title("Welcome to SENSE")

st.markdown(
    """
    Hallucinogenic substance use is widespread yet largely unsupervised, making it difficult to study in traditional clinical settings. To better understand 
    real-world experiences, RTI and NC State analyzed 29 million Reddit posts across 16 communities<sup>1</sup> discussing substances like psilocybin, LSD, 
    and ketamine. The Substance Effect Network and Sentiment Explorer Tool (SENSE) presents interactive dashboards that map reported effects and track user 
    sentiment over time.

    <h6> Substance Effect Network </h6>

    The Substance Effect Network maps user experiences with drugs by linking substances with their report effects. Positive pointwise mutual information (PPMI)
    offers a measure to compare the strengths of associations across substance-effect pairs. 

    <h6> Sentiment Explorer </h6>

    The Sentiment Explorer visualizes user sentiment of a given substance and changes over time. It provides an indication of whether user 
    experiences tend to become more positive, neutral, or remain the same with prolonged use. 

    <h6> Select a dashboard on the left to begin! </h6>

    Click [here](https://github.com/JohnETobin/SENSE) to view our papers and the Streamlit app repo. 

    <sup>1</sup> r/Ayahuasca, r/DMT, r/DXM, r/Ketamine, r/LSD, r/LSDTripLifeHacks, r/MDMA, r/Microdosing, r/Opiates, r/Psilocybin, 
    r/Psychedelics, r/Psychonaut, r/Salvia, r/Shrooms, r/TherapeuticKetamine, and r/Weed.
    """,
    unsafe_allow_html=True,
) 

# Footer text 
st.markdown("---") 

st.markdown(
    """
    <div style='text-align: center; font-size: 14px; color: gray;'>
        This is an open-source project. The code base is housed on GitHub.
    </div>
    """,
    unsafe_allow_html=True
)
