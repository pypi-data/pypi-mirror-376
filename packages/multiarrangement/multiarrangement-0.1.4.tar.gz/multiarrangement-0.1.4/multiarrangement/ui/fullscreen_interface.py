"""
Fullscreen interface for multiarrangement experiments.
"""

import pygame
import sys
from pathlib import Path
from .interface import BaseInterface
from ..core.experiment import MultiarrangementExperiment


class FullscreenInterface(BaseInterface):
    """Fullscreen interface for multiarrangement experiments."""
    
    def __init__(self, experiment: MultiarrangementExperiment):
        super().__init__(experiment)
        
        # Get screen dimensions
        info_object = pygame.display.Info()
        self.screen_width = info_object.current_w
        self.screen_height = info_object.current_h
        
        # Calculate arena parameters based on screen size
        self.arena_center = (self.screen_width // 2, self.screen_height // 2)
        self.arena_radius = min(self.screen_width, self.screen_height) // 2 - 100
        
    def setup_display(self) -> None:
        """Setup fullscreen display."""
        # Use borderless fullscreen (NOFRAME) to match set-cover behavior
        self.screen = pygame.display.set_mode((0, 0), pygame.NOFRAME)
        # Update stored dimensions from actual screen
        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        self.arena_center = (self.screen_width // 2, self.screen_height // 2)
        self.arena_radius = min(self.screen_width, self.screen_height) // 2 - 100
        pygame.display.set_caption("Multiarrangement Video Similarity Experiment - Fullscreen")
        
    def draw_interface(self) -> None:
        """Draw the fullscreen interface."""
        self.screen.fill(self.BLACK)
        
        # Draw arena circle
        pygame.draw.circle(self.screen, self.WHITE, self.arena_center, self.arena_radius, 4)
        
        # (Adaptive) No progress text at top-left
        
        # Draw video circles
        self.draw_video_circles()
        
        # Draw connections while dragging
        self.draw_connections_while_dragging(self.arena_center, self.arena_radius)
        
        # Draw done button (bottom-left)
        self.draw_done_button()
        
    def draw_done_button(self) -> None:
        """Draw the done button (match set-cover style)."""
        button_rect = pygame.Rect(50, self.screen_height - 100, 100, 50)
        
        # Check if completion criteria are met
        can_complete = self.check_completion_criteria(self.arena_center, self.arena_radius)
        button_color = self.GREEN if can_complete else self.RED
        
        pygame.draw.rect(self.screen, button_color, button_rect)
        pygame.draw.rect(self.screen, self.WHITE, button_rect, 2)
        
        text_surface = self.font.render("Done", True, self.WHITE)
        text_rect = text_surface.get_rect()
        text_rect.center = button_rect.center
        self.screen.blit(text_surface, text_rect)
        
        # Store button rect for click detection
        self.done_button_rect = button_rect
        
    def handle_events(self) -> None:
        """Handle pygame events for fullscreen interface."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_F11:
                    # Toggle fullscreen (though we start in fullscreen)
                    pass
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    pos = event.pos if hasattr(event, 'pos') else pygame.mouse.get_pos()
                    
                    # Check done button
                    if hasattr(self, 'done_button_rect') and self.done_button_rect.collidepoint(pos):
                        if self.check_completion_criteria(self.arena_center, self.arena_radius):
                            self.finish_batch()
                        continue
                    
                    # Handle double-click for video playback
                    handled = self.handle_double_click(pos)
                    
                    # Start dragging if not double-click
                    if not handled:
                        self.handle_drag_start(pos)
                        
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left click
                    self.handle_drag_end()
                    
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    pos = event.pos if hasattr(event, 'pos') else pygame.mouse.get_pos()
                    self.handle_drag_motion(pos)
                    
        # Arrange videos initially if not positioned
        if not self.video_positions and self.current_batch_videos:
            self.arrange_videos_in_circle(self.arena_center, self.arena_radius)

    def handle_double_click(self, pos):
        """Override: play videos in OpenCV popup (match set-cover)."""
        current_time = pygame.time.get_ticks()
        handled = False
        if current_time - self.last_click_time <= self.double_click_threshold:
            for i, video_filename in enumerate(self.current_batch_videos):
                video_name = Path(video_filename).stem
                if video_name in self.video_positions:
                    video_pos = self.video_positions[video_name]
                    distance = ((pos[0] - video_pos[0])**2 + (pos[1] - video_pos[1])**2) ** 0.5
                    if distance <= 40:
                        self.video_clicked[video_name] = True
                        video_path = self.experiment.get_video_path(video_filename)
                        suffix = Path(video_path).suffix.lower()
                        if suffix in {'.mp3', '.wav', '.ogg', '.flac', '.aac', '.m4a'}:
                            # Non-blocking audio playback to keep UI responsive
                            self.video_processor.play_audio_nonblocking(video_path)
                        else:
                            # OpenCV popup on top, 2x size, ESC/Space/q to close
                            self.video_processor.play_video_threaded(video_path)
                        handled = True
                        break
        self.last_click_time = current_time
        return handled
            
    def show_instructions(self) -> None:
        """Show fullscreen-optimized instructions (supports language/custom)."""
        # Custom instructions take precedence if provided
        if isinstance(getattr(self, "custom_instructions", None), list):
            for instruction in self.custom_instructions:
                self.show_instruction_screen(instruction)
            return

        lang = getattr(self.experiment, "language", "en")
        if lang == "tr":
            instructions = [
                "Video benzerliği düzenleme deneyine hoş geldiniz.",
                "Daire içinde videoları benzerliğe göre düzenleyeceksiniz.",
                "Önce gruptaki videoları izleyin, ardından sürükleyip yerleştirin.",
                "Benzer videoları yakın, farklı olanları uzak yerleştirin.",
                "Her bir daireye çift tıklayarak videoyu tekrar oynatın.",
                "Tüm videolar izlenmeli ve beyaz dairenin içinde kalmalıdır.",
                "Memnun kaldığınızda 'Bitti'ye tıklayın.",
                "Devam etmek için SPACE, çıkmak için ESC." 
            ]
        else:
            instructions = [
                "Welcome to the video similarity arrangement experiment.",
                "Arrange videos by similarity inside the white circle.",
                "First, watch each item; then drag circles to arrange them.",
                "Place similar videos close together; dissimilar far apart.",
                "Double-click any circle to replay its video.",
                "All circles must be watched and remain inside the white circle.",
                "Click 'Done' when you are satisfied.",
                "Press SPACE to continue, ESC to exit."
            ]

        for instruction in instructions:
            self.show_instruction_screen(instruction)
            
    def show_instruction_screen(self, message: str) -> None:
        """Show instruction screen optimized for fullscreen."""
        import textwrap
        
        waiting = True
        
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                        
            self.screen.fill(self.BLACK)
            
            # Wrap text for fullscreen display
            max_width = self.screen_width // 20  # Adjust for screen width
            lines = textwrap.wrap(message, width=max_width)
            
            # Calculate text positioning
            line_height = self.large_font.get_height()
            total_height = len(lines) * line_height
            start_y = (self.screen_height - total_height) // 2
            
            for i, line in enumerate(lines):
                text_surface = self.large_font.render(line, True, self.WHITE)
                text_rect = text_surface.get_rect()
                text_rect.centerx = self.screen_width // 2
                text_rect.y = start_y + i * line_height
                self.screen.blit(text_surface, text_rect)
                
            # Show continue instruction
            continue_text = "Press SPACE to continue, ESC to exit"
            continue_surface = self.font.render(continue_text, True, self.GRAY)
            continue_rect = continue_surface.get_rect()
            continue_rect.centerx = self.screen_width // 2
            continue_rect.y = self.screen_height - 100
            self.screen.blit(continue_surface, continue_rect)
                
            pygame.display.flip()
            self.clock.tick(60)
            
    def show_completion_message(self) -> None:
        """Show completion message optimized for fullscreen."""
        message = "Experiment completed!"
        subtitle = "Thank you for your participation."
        
        waiting = True
        start_time = pygame.time.get_ticks()
        
        while waiting and pygame.time.get_ticks() - start_time < 5000:  # Show for 5 seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.KEYDOWN:
                    waiting = False
                    
            self.screen.fill(self.BLACK)
            
            # Main message
            text_surface = pygame.font.Font(None, 72).render(message, True, self.GREEN)
            text_rect = text_surface.get_rect()
            text_rect.centerx = self.screen_width // 2
            text_rect.centery = self.screen_height // 2 - 50
            self.screen.blit(text_surface, text_rect)
            
            # Subtitle
            subtitle_surface = self.large_font.render(subtitle, True, self.WHITE)
            subtitle_rect = subtitle_surface.get_rect()
            subtitle_rect.centerx = self.screen_width // 2
            subtitle_rect.centery = self.screen_height // 2 + 50
            self.screen.blit(subtitle_surface, subtitle_rect)
            
            pygame.display.flip()
            self.clock.tick(60)
