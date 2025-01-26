"""Main class for generating books using AutoGen with improved iteration control"""
import autogen
from typing import Dict, List, Optional
import os
import time
import re

class BookGenerator:
    def __init__(self, agents: Dict[str, autogen.ConversableAgent], agent_config: Dict, outline: List[Dict]):
        """Initialize with outline to maintain chapter count context"""
        self.agents = agents
        self.agent_config = agent_config
        self.output_dir = "book_output"
        self.chapters_memory = []  # Store chapter summaries
        self.max_iterations = 3  # Limit editor-writer iterations
        self.outline = outline  # Store the outline
        os.makedirs(self.output_dir, exist_ok=True)

    def _clean_chapter_content(self, content: str) -> str:
        """Clean up chapter content by removing artifacts and chapter numbers"""
        # Remove chapter number references
        content = re.sub(r'\*?\s*\(Chapter \d+.*?\)', '', content)
        content = re.sub(r'\*?\s*Chapter \d+.*?\n', '', content, count=1)
        
        # Clean up any remaining markdown artifacts
        content = content.replace('*', '')
        content = content.strip()
        
        return content

    def _prepare_chapter_context(self, chapter_number: int, prompt: str) -> str:
        """Prepare context for chapter generation"""
        if chapter_number == 1:
            return f"Initial Chapter\nRequirements:\n{prompt}"
            
        context_parts = [
            "Previous Chapter Summaries:",
            *[f"Chapter {i+1}: {summary}" for i, summary in enumerate(self.chapters_memory)],
            "\nCurrent Chapter Requirements:",
            prompt
        ]
        return "\n".join(context_parts)

    def initiate_group_chat(self) -> autogen.GroupChat:
        """Create a new group chat for the agents with improved speaking order"""
        outline_context = "\n".join([
            f"\nChapter {ch['chapter_number']}: {ch['title']}\n{ch['prompt']}"
            for ch in sorted(self.outline, key=lambda x: x['chapter_number'])
        ])

        messages = [{
            "role": "system",
            "content": f"Complete Book Outline:\n{outline_context}"
        }]

        writer_final = autogen.AssistantAgent(
            name="writer_final",
            system_message=self.agents["writer"].system_message,
            llm_config=self.agent_config
        )
        
        return autogen.GroupChat(
            agents=[
                self.agents["user_proxy"],
                self.agents["memory_keeper"],
                self.agents["writer"],
                self.agents["editor"],
                writer_final
            ],
            messages=messages,
            max_round=5,
            speaker_selection_method="round_robin"
        )

    def _handle_chapter_generation_failure(self, chapter_number: int, prompt: str) -> None:
        """Handle failed chapter generation with simplified retry"""
        print(f"Attempting simplified retry for Chapter {chapter_number}...")
        
        try:
            # Create a new group chat with just essential agents
            retry_groupchat = autogen.GroupChat(
                agents=[
                    self.agents["user_proxy"],
                    self.agents["story_planner"],
                    self.agents["writer"]
                ],
                messages=[],
                max_round=3
            )
            
            manager = autogen.GroupChatManager(
                groupchat=retry_groupchat,
                llm_config={
                    "config_list": self.agent_config["config_list"],
                    "temperature": self.agent_config["temperature"],
                    "timeout": self.agent_config["timeout"],
                }
            )

            retry_prompt = f"""Emergency chapter generation for Chapter {chapter_number}.
            
{prompt}

Please generate this chapter in two steps:
1. Story Planner: Create a basic outline (tag: PLAN)
2. Writer: Write the complete chapter (tag: SCENE FINAL)

Keep it simple and direct."""

            self.agents["user_proxy"].initiate_chat(
                manager,
                message=retry_prompt
            )
            
            # Save the retry results
            self._process_chapter_results(chapter_number, retry_groupchat.messages)
            
        except Exception as e:
            print(f"Error in retry attempt for Chapter {chapter_number}: {str(e)}")
            print("Unable to generate chapter content after retry")

    def generate_chapter(self, chapter_number: int, prompt: str) -> None:
        """Generate a single chapter with completion verification"""
        print(f"\nGenerating Chapter {chapter_number}...")
        
        try:
            # Create group chat with reduced rounds
            groupchat = self.initiate_group_chat()
            manager = autogen.GroupChatManager(
                groupchat=groupchat,
                llm_config=self.agent_config
            )

            # Prepare context
            context = self._prepare_chapter_context(chapter_number, prompt)
            chapter_prompt = f"""
            IMPORTANT: Wait for confirmation before proceeding.
            IMPORTANT: This is Chapter {chapter_number}. Do not proceed to next chapter until explicitly instructed.
            DO NOT END THE STORY HERE unless this is actually the final chapter ({self.outline[-1]['chapter_number']}).

            Current Task: Generate Chapter {chapter_number} content only.

            Chapter Outline:
            Title: {self.outline[chapter_number - 1]['title']}

            Chapter Requirements:
            {prompt}

            Previous Context for Reference:
            {context}

            Follow this exact sequence for Chapter {chapter_number} only:

            1. Memory Keeper: Context (MEMORY UPDATE)
            2. Writer: Draft (CHAPTER)
            3. Editor: Review (FEEDBACK)
            4. Writer Final: Revision (CHAPTER FINAL)

            Wait for each step to complete before proceeding."""

            # Start generation
            self.agents["user_proxy"].initiate_chat(
                manager,
                message=chapter_prompt
            )

            if not self._verify_chapter_complete(groupchat.messages):
                raise ValueError(f"Chapter {chapter_number} generation incomplete")
        
            self._process_chapter_results(chapter_number, groupchat.messages)
            chapter_file = os.path.join(self.output_dir, f"chapter_{chapter_number:02d}.txt")
            if not os.path.exists(chapter_file):
                raise FileNotFoundError(f"Chapter {chapter_number} file not created")
        
            completion_msg = f"Chapter {chapter_number} is complete. Proceed with next chapter."
            self.agents["user_proxy"].send(completion_msg, manager)
            
        except Exception as e:
            print(f"Error in chapter {chapter_number}: {str(e)}")
            self._handle_chapter_generation_failure(chapter_number, prompt)

    def generate_book(self, outline: List[Dict]) -> None:
        """Generate the book with strict chapter sequencing"""
        print("\nStarting Book Generation...")
        print(f"Total chapters: {len(outline)}")
        
        # Sort outline by chapter number
        sorted_outline = sorted(outline, key=lambda x: x["chapter_number"])
        
        for chapter in sorted_outline:
            chapter_number = chapter["chapter_number"]
            
            # Verify previous chapter exists and is valid
            if chapter_number > 1:
                prev_file = os.path.join(self.output_dir, f"chapter_{chapter_number-1:02d}.txt")
                if not os.path.exists(prev_file):
                    print(f"Previous chapter {chapter_number-1} not found. Stopping.")
                    break
                    
                # Verify previous chapter content
                with open(prev_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not self._verify_chapter_content(content, chapter_number-1):
                        print(f"Previous chapter {chapter_number-1} content invalid. Stopping.")
                        break
            
            # Generate current chapter
            print(f"\n{'='*20} Chapter {chapter_number} {'='*20}")
            self.generate_chapter(chapter_number, chapter["prompt"])
            
            # Verify current chapter
            chapter_file = os.path.join(self.output_dir, f"chapter_{chapter_number:02d}.txt")
            if not os.path.exists(chapter_file):
                print(f"Failed to generate chapter {chapter_number}")
                break
                
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not self._verify_chapter_content(content, chapter_number):
                    print(f"Chapter {chapter_number} content invalid")
                    break
                    
            print(f"✓ Chapter {chapter_number} complete")
            time.sleep(5)

    def _verify_chapter_content(self, content: str, chapter_number: int) -> bool:
        """Verify chapter content is valid"""
        if not content:
            return False
            
        # Check for chapter header
        if f"Chapter {chapter_number}" not in content:
            return False
            
        # Ensure content isn't just metadata
        lines = content.split('\n')
        content_lines = [line for line in lines if line.strip() and 'MEMORY UPDATE:' not in line]
        
        return len(content_lines) >= 3  # At least chapter header + 2 content lines
