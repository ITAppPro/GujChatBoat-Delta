import pyttsx3

class VoiceHandler:
	def __init__(self):
		self.engine = pyttsx3.init()
		# Get available voices
		voices = self.engine.getProperty('voices')
		# Set default voice
		self.engine.setProperty('voice', voices[0].id)
		# Default rate
		self.engine.setProperty('rate', 150)
		# Set default volume
		self.engine.setProperty('volume', 1.0)
		
	def speak_fast(self, text, language='en'):
		"""
		Speak text at faster speed
		language: 'en' for English, 'gu' for Gujarati
		"""
		try:
			# Different rates for different languages
			if language == 'gu':
				self.engine.setProperty('rate', 150)  # Slower for Gujarati
			else:
				self.engine.setProperty('rate', 170)  # Faster for English
			
			# If Gujarati, use appropriate voice settings
			if language == 'gu':
				voices = self.engine.getProperty('voices')
				for voice in voices:
					if 'gujarati' in voice.name.lower():
						self.engine.setProperty('voice', voice.id)
						break
			
			self.engine.say(text)
			self.engine.runAndWait()
		except Exception as e:
			print(f"Error in fast speech: {str(e)}")

	def speak_slow(self, text, language='en'):
		"""
		Speak text at slower speed
		language: 'en' for English, 'gu' for Gujarati
		"""
		try:
			# Different rates for different languages
			if language == 'gu':
				self.engine.setProperty('rate', 120)  # Even slower for Gujarati
			else:
				self.engine.setProperty('rate', 130)  # Slow for English
			
			# If Gujarati, use appropriate voice settings
			if language == 'gu':
				voices = self.engine.getProperty('voices')
				for voice in voices:
					if 'gujarati' in voice.name.lower():
						self.engine.setProperty('voice', voice.id)
						break
			
			self.engine.say(text)
			self.engine.runAndWait()
		except Exception as e:
			print(f"Error in slow speech: {str(e)}")

	def set_volume(self, volume=1.0):
		"""Set the volume of speech (0.0 to 1.0)"""
		self.engine.setProperty('volume', volume)

# Usage example:
if __name__ == "__main__":
	voice_handler = VoiceHandler()
	
	# Test English
	voice_handler.speak_fast("This is a fast English test")
	voice_handler.speak_slow("This is a slow English test")
	
	# Test Gujarati
	voice_handler.speak_fast("આ ઝડપી ગુજરાતી ટેસ્ટ છે", language='gu')
	voice_handler.speak_slow("આ ધીમી ગુજરાતી ટેસ્ટ છે", language='gu')