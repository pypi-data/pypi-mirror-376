#!/usr/bin/env python3
"""
ctxzz Profile Card Generator
Usage: uvx ctxzz [effect]
"""

import sys
import time
import random

# terminaltexteffects v0.12.0 対応
try:
    from terminaltexteffects.effects.effect_matrix import Matrix
    from terminaltexteffects.effects.effect_fireworks import Fireworks
    from terminaltexteffects.effects.effect_waves import Waves
    from terminaltexteffects.effects.effect_decrypt import Decrypt
    from terminaltexteffects.effects.effect_slide import Slide
    from terminaltexteffects.effects.effect_rain import Rain
    from terminaltexteffects.effects.effect_print import Print
    from terminaltexteffects.effects.effect_wipe import Wipe
    from terminaltexteffects.effects.effect_beams import Beams
    from terminaltexteffects.effects.effect_bouncyballs import BouncyBalls
    from terminaltexteffects.effects.effect_bubbles import Bubbles
    from terminaltexteffects.effects.effect_burn import Burn
    from terminaltexteffects.effects.effect_crumble import Crumble
    from terminaltexteffects.effects.effect_errorcorrect import ErrorCorrect
    from terminaltexteffects.effects.effect_laseretch import LaserEtch
    from terminaltexteffects.effects.effect_overflow import Overflow
    from terminaltexteffects.effects.effect_scattered import Scattered
    from terminaltexteffects.effects.effect_spotlights import Spotlights
    from terminaltexteffects.effects.effect_sweep import Sweep
    from terminaltexteffects.effects.effect_vhstape import VHSTape
    from terminaltexteffects.utils import graphics
    TTE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  terminaltexteffects import error: {e}")
    TTE_AVAILABLE = False

def get_profile_text():
    """Atsushi Omata / ctxzzのプロフィール情報"""
    return """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🚀 Atsushi Omata / ctxzz 🚀                  ║
    ║                                                           ║
    ║               Welcome to my digital space!                ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  💼 Role        │  Assistant Professor                    ║
    ║  🌍 Location    │  Shizuoka, Japan                        ║
    ║  💡 Interests   │  Symbolic AI / HCI / Healthcare         ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║  🐙 GitHub      │  github.com/ctxzz                       ║
    ║  🐦 Twitter     │  @ctxzz                                 ║
    ║  🌟 Portfolio   │  omata.me                               ║
    ║  📧 Email       │  omata.atsushi.open@gmail.com           ║
    ║                                                           ║
    ╠═══════════════════════════════════════════════════════════╣
    ║                                                           ║
    ║         🟢 Status: ONLINE | Thanks for visiting! ✨       ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
"""

# フォールバック: シンプルなアニメーション効果
def show_simple_animation():
    """シンプルなアニメーション（3秒で完了）"""
    text = get_profile_text()
    
    # ターミナルをクリア
    print("\033[2J\033[H", end="")
    
    # テキストをそのまま表示（インデント保持）
    print(text)

def show_typewriter_fallback():
    """タイプライター風エフェクト（カスタム実装）- 8秒"""
    text = get_profile_text()
    
    # ターミナルをクリア
    print("\033[2J\033[H", end="")
    
    for char in text:
        print(char, end='', flush=True)
        if char == '\n':
            time.sleep(0.02)  # 0.05 -> 0.02 に短縮
        else:
            time.sleep(0.01)  # 0.02 -> 0.01 に短縮

def show_with_matrix_effect():
    """Matrix風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Matrix(text)
        effect.effect_config.rain_color = graphics.Color("00ff00")
        effect.effect_config.resolve_color = graphics.Color("ffffff")
        effect.effect_config.final_color = graphics.Color("00ff88")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Matrix effect error: {e}")
        show_simple_animation()

def show_with_decrypt_effect():
    """Decrypt風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Decrypt(text)
        effect.effect_config.ciphertext_colors = [
            graphics.Color("ff0080"),
            graphics.Color("8000ff"),
            graphics.Color("00ff80"),
            graphics.Color("ff8000"),
            graphics.Color("0080ff"),
            graphics.Color("ff0040")
        ]
        effect.effect_config.plaintext_color = graphics.Color("ffffff")
        effect.effect_config.final_color = graphics.Color("00ffaa")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Decrypt effect error: {e}")
        show_simple_animation()

def show_with_fireworks_effect():
    """Fireworks風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Fireworks(text)
        effect.effect_config.firework_colors = [
            graphics.Color("ff0080"),
            graphics.Color("8000ff"), 
            graphics.Color("00ff80"),
            graphics.Color("ff8000"),
            graphics.Color("0080ff"),
            graphics.Color("ffff00")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Fireworks effect error: {e}")
        show_simple_animation()

def show_with_waves_effect():
    """Waves風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Waves(text)
        effect.effect_config.wave_colors = [
            graphics.Color("00ffff"),
            graphics.Color("0080ff"),
            graphics.Color("8000ff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Waves effect error: {e}")
        show_simple_animation()

def show_with_slide_effect():
    """Slide風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Slide(text)
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Slide effect error: {e}")
        show_simple_animation()

def show_with_rain_effect():
    """Rain風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Rain(text)
        effect.effect_config.rain_colors = [
            graphics.Color("0080ff"),
            graphics.Color("00ffff"),
            graphics.Color("ffffff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Rain effect error: {e}")
        show_simple_animation()

def show_with_print_effect():
    """Print風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_typewriter_fallback()
        return
    
    text = get_profile_text()
    try:
        effect = Print(text)
        effect.effect_config.print_color = graphics.Color("00ff88")
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Print effect error: {e}")
        show_typewriter_fallback()

def show_with_beams_effect():
    """Beams風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Beams(text)
        effect.effect_config.beam_colors = [
            graphics.Color("ffff00"),
            graphics.Color("ff8800"),
            graphics.Color("ff0088")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Beams effect error: {e}")
        show_simple_animation()

def show_with_bouncyballs_effect():
    """BouncyBalls風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = BouncyBalls(text)
        effect.effect_config.ball_colors = [
            graphics.Color("ff0080"),
            graphics.Color("0080ff"),
            graphics.Color("80ff00"),
            graphics.Color("ff8000")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  BouncyBalls effect error: {e}")
        show_simple_animation()

def show_with_bubbles_effect():
    """Bubbles風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Bubbles(text)
        effect.effect_config.bubble_colors = [
            graphics.Color("00ffff"),
            graphics.Color("0080ff"),
            graphics.Color("8000ff"),
            graphics.Color("ff00ff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Bubbles effect error: {e}")
        show_simple_animation()

def show_with_burn_effect():
    """Burn風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Burn(text)
        effect.effect_config.burn_colors = [
            graphics.Color("ff0000"),
            graphics.Color("ff8000"),
            graphics.Color("ffff00"),
            graphics.Color("ffffff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Burn effect error: {e}")
        show_simple_animation()

def show_with_crumble_effect():
    """Crumble風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Crumble(text)
        effect.effect_config.crumble_colors = [
            graphics.Color("8b4513"),
            graphics.Color("a0522d"),
            graphics.Color("cd853f"),
            graphics.Color("deb887")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Crumble effect error: {e}")
        show_simple_animation()

def show_with_errorcorrect_effect():
    """ErrorCorrect風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = ErrorCorrect(text)
        effect.effect_config.error_color = graphics.Color("ff0000")
        effect.effect_config.correct_color = graphics.Color("00ff00")
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  ErrorCorrect effect error: {e}")
        show_simple_animation()

def show_with_laseretch_effect():
    """LaserEtch風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = LaserEtch(text)
        effect.effect_config.laser_color = graphics.Color("ff0000")
        effect.effect_config.etched_color = graphics.Color("ffffff")
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  LaserEtch effect error: {e}")
        show_simple_animation()

def show_with_overflow_effect():
    """Overflow風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Overflow(text)
        effect.effect_config.overflow_colors = [
            graphics.Color("ff0000"),
            graphics.Color("ff4000"),
            graphics.Color("ff8000"),
            graphics.Color("ffff00")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Overflow effect error: {e}")
        show_simple_animation()

def show_with_scattered_effect():
    """Scattered風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Scattered(text)
        effect.effect_config.scattered_colors = [
            graphics.Color("ff0080"),
            graphics.Color("8000ff"),
            graphics.Color("00ff80"),
            graphics.Color("ff8000")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Scattered effect error: {e}")
        show_simple_animation()

def show_with_spotlights_effect():
    """Spotlights風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Spotlights(text)
        effect.effect_config.spotlight_colors = [
            graphics.Color("ffffff"),
            graphics.Color("ffff00"),
            graphics.Color("00ffff"),
            graphics.Color("ff00ff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Spotlights effect error: {e}")
        show_simple_animation()

def show_with_sweep_effect():
    """Sweep風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Sweep(text)
        effect.effect_config.sweep_colors = [
            graphics.Color("00ff00"),
            graphics.Color("00ff80"),
            graphics.Color("00ffff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Sweep effect error: {e}")
        show_simple_animation()

def show_with_vhstape_effect():
    """VHSTape風エフェクト"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = VHSTape(text)
        effect.effect_config.glitch_colors = [
            graphics.Color("ff0080"),
            graphics.Color("00ff80"),
            graphics.Color("8000ff")
        ]
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  VHSTape effect error: {e}")
        show_simple_animation()

def show_with_wipe_effect():
    """Wipe風エフェクト（シンプル版）"""
    if not TTE_AVAILABLE:
        show_simple_animation()
        return
    
    text = get_profile_text()
    try:
        effect = Wipe(text)
        effect.effect_config.wipe_color = graphics.Color("ff8000")
        effect.effect_config.final_color = graphics.Color("ffffff")
        
        with effect.terminal_output() as terminal:
            for frame in effect:
                terminal.print(frame)
                
    except Exception as e:
        print(f"⚠️  Wipe effect error: {e}")
        show_simple_animation()

def show_random_effect():
    """利用可能なエフェクトからランダムに選択"""
    if TTE_AVAILABLE:
        effects = [
            show_with_matrix_effect,
            show_with_decrypt_effect,
            show_with_fireworks_effect,
            show_with_waves_effect,
            show_with_slide_effect,
            show_with_rain_effect,
            show_with_print_effect,
            show_with_wipe_effect,
            show_with_beams_effect,
            show_with_bouncyballs_effect,
            show_with_bubbles_effect,
            show_with_burn_effect,
            show_with_crumble_effect,
            show_with_errorcorrect_effect,
            show_with_laseretch_effect,
            show_with_overflow_effect,
            show_with_scattered_effect,
            show_with_spotlights_effect,
            show_with_sweep_effect,
            show_with_vhstape_effect,
            show_simple_animation  # シンプル版も含める
        ]
    else:
        effects = [show_simple_animation, show_typewriter_fallback]
    
    random.choice(effects)()

def list_available_effects():
    """利用可能なエフェクトを表示"""
    print("Available effects:")
    
    if TTE_AVAILABLE:
        effects = [
            "matrix", "decrypt", "fireworks", "waves", 
            "slide", "rain", "print", "wipe", "typewriter", 
            "beams", "bouncyballs", "bubbles", "burn", "crumble",
            "errorcorrect", "laseretch", "overflow", "scattered",
            "spotlights", "sweep", "vhstape",
            "simple", "random"
        ]
    else:
        effects = ["simple", "typewriter", "random"]
    
    for effect in effects:
        print(f"  {effect}")

def main():
    """メイン関数"""
    # ターミナルをクリア
    print("\033[2J\033[H", end="")
    
    if len(sys.argv) > 1:
        effect_type = sys.argv[1].lower()
        
        if effect_type == "matrix":
            show_with_matrix_effect()
        elif effect_type == "decrypt":
            show_with_decrypt_effect()
        elif effect_type == "fireworks":
            show_with_fireworks_effect()
        elif effect_type == "waves":
            show_with_waves_effect()
        elif effect_type == "slide":
            show_with_slide_effect()
        elif effect_type == "rain":
            show_with_rain_effect()
        elif effect_type == "print":
            show_with_print_effect()
        elif effect_type == "wipe":
            show_with_wipe_effect()
        elif effect_type == "beams":
            show_with_beams_effect()
        elif effect_type == "bouncyballs":
            show_with_bouncyballs_effect()
        elif effect_type == "bubbles":
            show_with_bubbles_effect()
        elif effect_type == "burn":
            show_with_burn_effect()
        elif effect_type == "crumble":
            show_with_crumble_effect()
        elif effect_type == "errorcorrect":
            show_with_errorcorrect_effect()
        elif effect_type == "laseretch":
            show_with_laseretch_effect()
        elif effect_type == "overflow":
            show_with_overflow_effect()
        elif effect_type == "scattered":
            show_with_scattered_effect()
        elif effect_type == "spotlights":
            show_with_spotlights_effect()
        elif effect_type == "sweep":
            show_with_sweep_effect()
        elif effect_type == "vhstape":
            show_with_vhstape_effect()
        elif effect_type == "typewriter":
            show_typewriter_fallback()
        elif effect_type == "simple":
            show_simple_animation()
        elif effect_type == "random":
            show_random_effect()
        elif effect_type in ["help", "-h", "--help"]:
            list_available_effects()
        else:
            print(f"⚠️  Effect '{effect_type}' not available.")
            list_available_effects()
    else:
        show_random_effect()

if __name__ == "__main__":
    main()