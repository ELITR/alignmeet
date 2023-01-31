import numpy as np
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer
import pickle
#TODO: dependencies

class Embedder:
    def __init__(self, model = 'stsb-mpnet-base-v2'):
        self.model_name = model
        self.model = SentenceTransformer(model)
        
    def embed(self, lines):
        embeds = self.model.encode([l.text for l in lines])
        return embeds
    
    @staticmethod
    def saveEmbed(embeds, filename):
        with open(filename, 'wb') as f:
            pickle.dump(embeds, f) #TODO: do this properly
    
    @staticmethod
    def loadEmbed(filename):
        with open(filename, 'rb') as f:
            embeds = pickle.load(f)
        return embeds
    
class Aligner:
    @staticmethod
    def align(transcript_das, minutes, transcript_emb, minutes_emb, threshold = 0.5, disregard_existing_align = False, final=False):
        alignments = np.zeros(len(transcript_emb))
        for i, te in enumerate(transcript_emb):
            sims = np.zeros(len(minutes_emb))
            for j, se in enumerate(minutes_emb):
                sims[j] = cosine(te, se)
            if sims.min() < threshold:
                alignments[i] = np.argmin(sims) + 1
        for i, alignment in enumerate(alignments):
            if transcript_das[i].minute == None or transcript_das[i].is_tentative or disregard_existing_align:
                if alignment == 0:
                    transcript_das[i].minute = None
                    transcript_das[i].is_tentative = False
                else:
                    transcript_das[i].minute = minutes[alignment-1]
                    transcript_das[i].is_tentative = not final
    
    @staticmethod       
    def align(transcript_emb, minutes_emb, threshold = 0.5):
        alignments = np.zeros(len(transcript_emb))
        for i, te in enumerate(transcript_emb):
            sims = np.zeros(len(minutes_emb))
            for j, se in enumerate(minutes_emb):
                sims[j] = cosine(te, se)
            if sims.min() < threshold:
                alignments[i] = np.argmin(sims) + 1
        return alignments
            