import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
import threading
import json
from datetime import datetime
import platform

# Try to import appropriate TTS for the platform
TTS_ENGINE = None
if platform.system() == "Windows":
    try:
        import win32com.client
        TTS_ENGINE = "windows"
    except ImportError:
        print("win32com not available. Install with: pip install pywin32")
else:
    try:
        import pyttsx3
        TTS_ENGINE = "pyttsx3"
    except ImportError:
        print("pyttsx3 not available. Install with: pip install pyttsx3")

class ModernButton(tk.Button):
    """Custom modern button with hover effects"""
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
    
    def on_enter(self, e):
        if self['state'] == 'normal':
            self['background'] = self['activebackground']
    
    def on_leave(self, e):
        self['background'] = self.defaultBackground

class AIInterviewer:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Voice Interviewer")
        self.root.geometry("900x700")
        
        # Color scheme
        self.colors = {
            'primary': '#6C5CE7',      # Purple
            'secondary': '#00B894',     # Green
            'accent': '#FDCB6E',        # Yellow
            'danger': '#FF7675',        # Red
            'dark': '#2D3436',          # Dark gray
            'light': '#DFE6E9',         # Light gray
            'white': '#FFFFFF',
            'text_dark': '#2D3436',
            'text_light': '#636E72',
            'bg': '#F5F6FA'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Initialize speech components
        self.recognizer = sr.Recognizer()
        self.tts_enabled = False
        self.tts_engine_type = TTS_ENGINE
        
        # Initialize TTS based on platform
        if TTS_ENGINE == "windows":
            try:
                self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
                self.speaker.Rate = 1
                self.speaker.Volume = 90
                self.tts_enabled = True
            except Exception as e:
                self.show_tts_warning(str(e))
        elif TTS_ENGINE == "pyttsx3":
            try:
                import pyttsx3
                self.engine = pyttsx3.init()
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.9)
                self.tts_enabled = True
            except Exception as e:
                self.show_tts_warning(str(e))
        
        # Interview state
        self.questions = []
        self.current_question_index = 0
        self.answers = []
        self.is_listening = False
        self.interview_started = False
        self.setup_mode = True  # Start in setup mode
        
        self.setup_ui()
    
    def show_tts_warning(self, error_msg):
        """Show warning about TTS not being available"""
        messagebox.showinfo(
            "Voice Output Disabled",
            f"Text-to-speech is not available.\n\n"
            f"Questions will be displayed on screen.\n\n"
            f"For Windows: pip install pywin32\n"
            f"For others: pip install pyttsx3"
        )
        
    def setup_ui(self):
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Header
        self.create_header(main_container)
        
        # Content area (will switch between setup and interview)
        self.content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        self.content_frame.pack(fill='both', expand=True, pady=20)
        
        # Show setup screen initially
        self.show_setup_screen()
    
    def create_header(self, parent):
        """Create the header section"""
        header_frame = tk.Frame(parent, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title with icon
        title_container = tk.Frame(header_frame, bg=self.colors['bg'])
        title_container.pack()
        
        title_label = tk.Label(
            title_container,
            text="🎙️ AI Voice Interviewer",
            font=("Segoe UI", 32, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_label.pack()
        
        subtitle = tk.Label(
            title_container,
            text="Professional Interview Assistant",
            font=("Segoe UI", 12),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        subtitle.pack()
        
        # Status bar
        self.status_bar = tk.Frame(header_frame, bg=self.colors['white'], height=50)
        self.status_bar.pack(fill='x', pady=(15, 0))
        
        # TTS Status
        tts_icon = "🔊" if self.tts_enabled else "🔇"
        tts_text = "Voice Enabled" if self.tts_enabled else "Screen Only"
        tts_color = self.colors['secondary'] if self.tts_enabled else self.colors['text_light']
        
        tts_status = tk.Label(
            self.status_bar,
            text=f"{tts_icon} {tts_text}",
            font=("Segoe UI", 10),
            bg=self.colors['white'],
            fg=tts_color
        )
        tts_status.pack(side='left', padx=15, pady=10)
        
        # Progress indicator (hidden initially)
        self.progress_label = tk.Label(
            self.status_bar,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=self.colors['white'],
            fg=self.colors['primary']
        )
        self.progress_label.pack(side='right', padx=15, pady=10)
    
    def show_setup_screen(self):
        """Show the question setup screen"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Setup container
        setup_container = tk.Frame(self.content_frame, bg=self.colors['white'])
        setup_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Instructions
        instruction_label = tk.Label(
            setup_container,
            text="📝 Enter Your Interview Questions",
            font=("Segoe UI", 18, "bold"),
            bg=self.colors['white'],
            fg=self.colors['text_dark']
        )
        instruction_label.pack(pady=20)
        
        subtitle_label = tk.Label(
            setup_container,
            text="Enter one question per line. The AI will ask them one by one.",
            font=("Segoe UI", 11),
            bg=self.colors['white'],
            fg=self.colors['text_light']
        )
        subtitle_label.pack(pady=(0, 20))
        
        # Text input area with custom styling - Fixed height
        text_container = tk.Frame(setup_container, bg=self.colors['white'], height=300)
        text_container.pack(fill='x', padx=40, pady=(0, 20))
        text_container.pack_propagate(False)  # Prevent container from shrinking
        
        # Scrollbar
        scrollbar = tk.Scrollbar(text_container)
        scrollbar.pack(side='right', fill='y')
        
        self.questions_text = tk.Text(
            text_container,
            font=("Segoe UI", 12),
            wrap='word',
            yscrollcommand=scrollbar.set,
            relief='flat',
            padx=15,
            pady=15,
            bg='#F8F9FA',
            fg=self.colors['text_dark'],
            insertbackground=self.colors['primary'],
            selectbackground=self.colors['primary'],
            selectforeground='white'
        )
        self.questions_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.questions_text.yview)
        
        # Sample questions
        sample_questions = """Tell me about yourself.
What are your key strengths?
Describe a challenging project you worked on.
Where do you see yourself in 5 years?
Why do you want to work with us?"""
        self.questions_text.insert("1.0", sample_questions)
        
        # Start button - Now clearly visible
        start_btn_container = tk.Frame(setup_container, bg=self.colors['white'])
        start_btn_container.pack(pady=30)
        
        self.start_btn = ModernButton(
            start_btn_container,
            text="🚀 Start Interview",
            command=self.start_interview,
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['primary'],
            fg='white',
            activebackground='#5F4FD1',
            activeforeground='white',
            padx=40,
            pady=15,
            relief='flat',
            cursor="hand2",
            borderwidth=0
        )
        self.start_btn.pack()
    
    def show_interview_screen(self):
        """Show the interview screen with current question"""
        # Clear content frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Interview container
        interview_container = tk.Frame(self.content_frame, bg=self.colors['bg'])
        interview_container.pack(fill='both', expand=True)
        
        # Question card
        question_card = tk.Frame(
            interview_container,
            bg=self.colors['white'],
            relief='flat',
            borderwidth=0
        )
        question_card.pack(fill='both', expand=True, pady=(0, 20))
        
        # Question header
        question_header = tk.Frame(question_card, bg=self.colors['primary'], height=60)
        question_header.pack(fill='x')
        question_header.pack_propagate(False)
        
        tk.Label(
            question_header,
            text="💭 Current Question",
            font=("Segoe UI", 14, "bold"),
            bg=self.colors['primary'],
            fg='white'
        ).pack(pady=15)
        
        # Question text
        question_text_frame = tk.Frame(question_card, bg=self.colors['white'])
        question_text_frame.pack(fill='both', expand=True, padx=40, pady=40)
        
        self.current_question_label = tk.Label(
            question_text_frame,
            text="",
            font=("Segoe UI", 20),
            bg=self.colors['white'],
            fg=self.colors['text_dark'],
            wraplength=700,
            justify='center'
        )
        self.current_question_label.pack(expand=True)
        
        # Answer card
        answer_card = tk.Frame(
            interview_container,
            bg=self.colors['white'],
            relief='flat',
            borderwidth=0
        )
        answer_card.pack(fill='both', pady=(0, 20))
        
        # Answer header
        answer_header = tk.Frame(answer_card, bg=self.colors['secondary'], height=50)
        answer_header.pack(fill='x')
        answer_header.pack_propagate(False)
        
        tk.Label(
            answer_header,
            text="✅ Your Answer",
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['secondary'],
            fg='white'
        ).pack(pady=12)
        
        # Answer text area
        answer_text_frame = tk.Frame(answer_card, bg=self.colors['white'])
        answer_text_frame.pack(fill='both', padx=20, pady=20)
        
        self.answer_text = tk.Text(
            answer_text_frame,
            font=("Segoe UI", 11),
            wrap='word',
            height=4,
            relief='flat',
            padx=15,
            pady=15,
            bg='#F8F9FA',
            fg=self.colors['text_dark'],
            state='disabled'
        )
        self.answer_text.pack(fill='both')
        
        # Control buttons
        controls_frame = tk.Frame(interview_container, bg=self.colors['bg'])
        controls_frame.pack(fill='x', pady=10)
        
        # Center the buttons
        button_container = tk.Frame(controls_frame, bg=self.colors['bg'])
        button_container.pack()
        
        self.listen_btn = ModernButton(
            button_container,
            text="🎤 Listen to Answer",
            command=self.listen_to_answer,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['secondary'],
            fg='white',
            activebackground='#00A383',
            activeforeground='white',
            padx=25,
            pady=12,
            relief='flat',
            cursor="hand2",
            borderwidth=0
        )
        self.listen_btn.grid(row=0, column=0, padx=8)
        
        self.next_btn = ModernButton(
            button_container,
            text="Next Question →",
            command=self.next_question,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['accent'],
            fg=self.colors['text_dark'],
            activebackground='#FDC453',
            activeforeground=self.colors['text_dark'],
            padx=25,
            pady=12,
            relief='flat',
            cursor="hand2",
            borderwidth=0
        )
        self.next_btn.grid(row=0, column=1, padx=8)
        
        self.finish_btn = ModernButton(
            button_container,
            text="✓ Finish Interview",
            command=self.finish_interview,
            font=("Segoe UI", 12, "bold"),
            bg=self.colors['danger'],
            fg='white',
            activebackground='#FF6B6B',
            activeforeground='white',
            padx=25,
            pady=12,
            relief='flat',
            cursor="hand2",
            borderwidth=0
        )
        self.finish_btn.grid(row=0, column=2, padx=8)
        
        # Status message
        self.status_message = tk.Label(
            interview_container,
            text="🎯 Ready to record your answer",
            font=("Segoe UI", 11),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        self.status_message.pack(pady=15)
    
    def speak(self, text):
        """Convert text to speech"""
        if not self.tts_enabled:
            print(f"[AI Says]: {text}")
            return
        
        def _speak():
            try:
                if self.tts_engine_type == "windows":
                    self.speaker.Speak(text)
                elif self.tts_engine_type == "pyttsx3":
                    self.engine.say(text)
                    self.engine.runAndWait()
            except Exception as e:
                print(f"TTS Error: {e}")
        
        thread = threading.Thread(target=_speak)
        thread.start()
    
    def start_interview(self):
        """Initialize and start the interview"""
        # Get questions from text box
        questions_input = self.questions_text.get("1.0", tk.END).strip()
        self.questions = [q.strip() for q in questions_input.split('\n') if q.strip()]
        
        if not self.questions:
            messagebox.showwarning("No Questions", "Please enter at least one question!")
            return
        
        # Reset state
        self.current_question_index = 0
        self.answers = []
        self.interview_started = True
        self.setup_mode = False
        
        # Switch to interview screen
        self.show_interview_screen()
        
        # Ask first question
        self.ask_current_question()
    
    def ask_current_question(self):
        """Ask the current question"""
        if self.current_question_index < len(self.questions):
            question = self.questions[self.current_question_index]
            self.current_question_label.config(text=question)
            self.progress_label.config(
                text=f"Question {self.current_question_index + 1} of {len(self.questions)}"
            )
            
            # Clear previous answer
            self.answer_text.config(state="normal")
            self.answer_text.delete("1.0", tk.END)
            self.answer_text.config(state="disabled")
            
            # Speak the question
            self.status_message.config(
                text="🎙️ AI is asking the question...",
                fg=self.colors['primary']
            )
            self.speak(f"Question {self.current_question_index + 1}. {question}")
            
            # Update status after speaking
            self.root.after(2000, lambda: self.status_message.config(
                text="🎯 Ready to record your answer",
                fg=self.colors['text_light']
            ))
        else:
            self.finish_interview()
    
    def listen_to_answer(self):
        """Listen to candidate's voice answer"""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.listen_btn.config(
            state="disabled",
            text="🎤 Listening...",
            bg='#95A5A6'
        )
        self.status_message.config(
            text="🎤 Listening... Please speak clearly",
            fg=self.colors['secondary']
        )
        
        def _listen():
            try:
                with sr.Microphone() as source:
                    # Adjust for ambient noise
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    # Listen for answer
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=60)
                    
                    # Recognize speech
                    self.root.after(0, lambda: self.status_message.config(
                        text="⚙️ Processing your answer...",
                        fg=self.colors['accent']
                    ))
                    
                    answer = self.recognizer.recognize_google(audio)
                    
                    # Update UI with answer
                    self.root.after(0, lambda: self.display_answer(answer))
                    
            except sr.WaitTimeoutError:
                self.root.after(0, lambda: self.status_message.config(
                    text="⚠️ No speech detected. Please try again.",
                    fg=self.colors['danger']
                ))
                self.root.after(0, lambda: messagebox.showwarning(
                    "Timeout", "No speech detected. Please click 'Listen to Answer' again."
                ))
            except sr.UnknownValueError:
                self.root.after(0, lambda: self.status_message.config(
                    text="⚠️ Could not understand. Please try again.",
                    fg=self.colors['danger']
                ))
                self.root.after(0, lambda: messagebox.showwarning(
                    "Not Understood", "Could not understand the audio. Please speak clearly and try again."
                ))
            except sr.RequestError as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.status_message.config(
                    text="❌ Speech recognition error",
                    fg=self.colors['danger']
                ))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                    "Error", f"Speech recognition error: {msg}"
                ))
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.status_message.config(
                    text="❌ An error occurred",
                    fg=self.colors['danger']
                ))
                self.root.after(0, lambda msg=error_msg: messagebox.showerror(
                    "Error", f"An error occurred: {msg}"
                ))
            finally:
                self.is_listening = False
                self.root.after(0, lambda: self.listen_btn.config(
                    state="normal",
                    text="🎤 Listen to Answer",
                    bg=self.colors['secondary']
                ))
        
        thread = threading.Thread(target=_listen)
        thread.start()
    
    def display_answer(self, answer):
        """Display the recognized answer"""
        self.answer_text.config(state="normal")
        self.answer_text.delete("1.0", tk.END)
        self.answer_text.insert("1.0", answer)
        self.answer_text.config(state="disabled")
        
        # Store answer
        self.answers.append({
            "question": self.questions[self.current_question_index],
            "answer": answer,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        self.status_message.config(
            text="✅ Answer recorded successfully!",
            fg=self.colors['secondary']
        )
        self.speak("Thank you. I've recorded your answer.")
    
    def next_question(self):
        """Move to the next question"""
        if self.current_question_index < len(self.answers):
            # Answer has been recorded for current question
            self.current_question_index += 1
            if self.current_question_index < len(self.questions):
                self.ask_current_question()
            else:
                messagebox.showinfo(
                    "Interview Complete",
                    "All questions have been asked!\n\nClick 'Finish Interview' to save results."
                )
                self.listen_btn.config(state="disabled")
                self.next_btn.config(state="disabled")
        else:
            messagebox.showwarning(
                "No Answer",
                "Please record an answer before moving to the next question."
            )
    
    def finish_interview(self):
        """Finish the interview and save results"""
        if not self.answers:
            messagebox.showwarning("No Answers", "No answers have been recorded yet!")
            return
        
        # Save to JSON file in current directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"interview_results_{timestamp}.json"
        
        results = {
            "interview_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_questions": len(self.questions),
            "answered_questions": len(self.answers),
            "qa_pairs": self.answers
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.speak("Interview completed. Thank you for your time.")
            
            # Get absolute path for display
            import os
            abs_path = os.path.abspath(filename)
            
            messagebox.showinfo(
                "🎉 Interview Complete!",
                f"Interview finished successfully!\n\n"
                f"✅ Answered: {len(self.answers)}/{len(self.questions)} questions\n\n"
                f"📁 Results saved to:\n{abs_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Save Error",
                f"Could not save results: {e}\n\n"
                f"Your interview data is still in memory."
            )
        
        # Reset UI
        self.reset_interview()
    
    def reset_interview(self):
        """Reset the interview to initial state"""
        self.interview_started = False
        self.current_question_index = 0
        self.answers = []
        self.setup_mode = True
        
        self.progress_label.config(text="")
        
        # Return to setup screen
        self.show_setup_screen()


def main():
    root = tk.Tk()
    
    # Center window on screen
    window_width = 900
    window_height = 700
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    app = AIInterviewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
