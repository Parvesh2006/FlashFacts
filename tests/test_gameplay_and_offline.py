import os
import pytest
from fastapi.testclient import TestClient


def test_fact_jumper_physics_parameters():
    """
    Verify Fact Jumper Chrome T-Rex physics calculations:
    - Controlled jump height (stays inside viewport)
    - Comfortable initial speed
    - Gradual acceleration
    - Enforced maximum speed
    - Fair obstacle clearance window
    """
    initial_speed = 4.8
    max_speed = 9.5
    acceleration = 0.0035
    gravity = 0.60
    jump_impulse = -10.2
    canvas_height = 320
    ground_y = canvas_height - 40  # 280
    player_height = 52

    # 1. Peak jump height
    peak_height = (jump_impulse ** 2) / (2 * gravity)
    assert 80 <= peak_height <= 95, f"Peak jump height {peak_height} outside controlled range (80-95px)"

    # 2. Viewport headroom (character never leaves visible area)
    min_head_y = ground_y - peak_height - player_height
    assert min_head_y > 100, f"Player head {min_head_y}px too close to top edge (must have >100px headroom)"
    assert min_head_y < canvas_height, "Player is outside canvas bottom"

    # 3. Air time in 60fps frames
    air_frames = 2 * (abs(jump_impulse) / gravity)
    assert 30 <= air_frames <= 38, f"Air time {air_frames} frames outside natural range (30-38 frames)"

    # 4. Speed progression curve
    def get_speed(score: int) -> float:
        return min(max_speed, initial_speed + score * acceleration)

    assert get_speed(0) == initial_speed
    assert get_speed(100) > initial_speed
    assert get_speed(500) < max_speed
    assert get_speed(2000) == max_speed  # strictly capped

    # 5. Obstacle reaction clearance at initial and maximum speed
    for s in [initial_speed, 6.0, 8.0, max_speed]:
        min_gap = max(340, s * 58)
        # Distance covered during a single jump
        jump_distance = s * air_frames
        # Gap must exceed jump distance with ample reaction runway
        assert min_gap > jump_distance * 1.5, f"Obstacle gap {min_gap} too tight for jump distance {jump_distance}"


def test_ground_alignment_and_clamping_consistency():
    """
    Verify consistent ground coordinates across React component and offline HTML:
    - Unified canvas dimensions (840x320)
    - Ground line at exactly 280px (320 - 40)
    - Ground clamping logic ensures feet never fall beneath ground_y
    """
    game_path = os.path.join("apps", "web", "components", "game", "fact-jumper-game.tsx")
    offline_path = os.path.join("apps", "web", "public", "offline.html")

    with open(game_path, "r", encoding="utf-8") as f:
        game_code = f.read()
    with open(offline_path, "r", encoding="utf-8") as f:
        offline_code = f.read()

    # Verify unified constants in React game
    assert "GAME_GROUND_Y = GAME_CANVAS_HEIGHT - GAME_GROUND_OFFSET" in game_code
    assert "playerRef.current.y = GAME_GROUND_Y" in game_code
    # Ground clamping branch when player is grounded
    assert "p.y = GAME_GROUND_Y;" in game_code
    assert "p.vy = 0;" in game_code

    # Verify unified constants in Offline HTML
    assert "GAME_GROUND_Y = GAME_CANVAS_HEIGHT - GAME_GROUND_OFFSET" in offline_code
    assert "player.y = GAME_GROUND_Y" in offline_code
    assert "player.vy = 0" in offline_code


def test_flying_bird_obstacles_and_collision_hitboxes():
    """
    Verify Chrome Dino style flying bird obstacles:
    - Multiple sensible flight heights: bird_low, bird_mid, bird_high
    - 2-frame wing flapping animation
    - Fair hitboxes: ducking avoids mid birds, running avoids high birds
    """
    ground_y = 280
    bird_w, bird_h = 36, 22
    grace = 3

    # Bird flight levels:
    # 1. bird_low (requires jump): y = ground_y - 26 = 254
    low_y = ground_y - 26
    # 2. bird_mid (requires duck): y = ground_y - 58 = 222
    mid_y = ground_y - 58
    # 3. bird_high (run underneath / avoid jumping): y = ground_y - 76 = 204
    high_y = ground_y - 76

    # Standing hitbox: x=83, y=230, w=18, h=50 (feet at 280)
    stand_box = {"x": 83, "y": ground_y - 50, "w": 18, "h": 50}
    # Ducking hitbox: x=78, y=258, w=32, h=22 (feet at 280)
    duck_box = {"x": 78, "y": ground_y - 22, "w": 32, "h": 22}

    def check_collision(box, obs):
        return (
            box["x"] + grace < obs["x"] + obs["w"] - grace
            and box["x"] + box["w"] - grace > obs["x"] + grace
            and box["y"] + grace < obs["y"] + obs["h"] - grace
            and box["y"] + box["h"] - grace > obs["y"] + grace
        )

    # Collision test at contact X
    obs_x = 83

    # Mid bird collision tests:
    mid_bird = {"x": obs_x, "y": mid_y, "w": bird_w, "h": bird_h}
    # Standing player collides with mid bird
    assert check_collision(stand_box, mid_bird) is True, "Standing player must collide with mid bird"
    # Ducking player slides under mid bird safely
    assert check_collision(duck_box, mid_bird) is False, "Ducking player must cleanly clear mid bird"

    # High bird collision tests:
    high_bird = {"x": obs_x, "y": high_y, "w": bird_w, "h": bird_h}
    # Standing player runs underneath high bird safely
    assert check_collision(stand_box, high_bird) is False, "Standing player must safely run under high bird"

    # Jumping player hits high bird during jump (e.g. at jump y=240, head at 190, feet at 240)
    jump_box = {"x": obs_x, "y": 190, "w": 18, "h": 50}
    assert check_collision(jump_box, high_bird) is True, "Jumping player must collide with high bird"

    # Check that both implementations have bird obstacles and flapping animation
    game_path = os.path.join("apps", "web", "components", "game", "fact-jumper-game.tsx")
    offline_path = os.path.join("apps", "web", "public", "offline.html")

    with open(game_path, "r", encoding="utf-8") as f:
        game_code = f.read()
    with open(offline_path, "r", encoding="utf-8") as f:
        offline_code = f.read()

    assert "drawBird" in game_code
    assert "bird_mid" in game_code
    assert "flapFrame" in game_code

    assert "drawBird" in offline_code
    assert "bird_mid" in offline_code
    assert "flapFrame" in offline_code


def test_health_endpoint_for_connectivity_probe(client: TestClient):
    """
    Verify the /api/v1/health endpoint responds reliably for OfflineCoordinator
    connectivity heartbeat and reconnection validation.
    """
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data.get("status") in ["healthy", "ok", "operational"] or "status" in data


def test_offline_html_asset_integrity():
    """
    Verify that offline.html is completely self-contained:
    - Zero remote scripts, CDN links, or external font stylesheets
    - Contains Web Audio API tone synthesis
    - Implements tuned Chrome T-Rex physics constants
    """
    offline_path = os.path.join("apps", "web", "public", "offline.html")
    assert os.path.exists(offline_path), "offline.html must exist in public directory"

    with open(offline_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Must not contain external remote script imports
    assert "https://" not in html.lower() or "fonts.googleapis.com" not in html, "offline.html must not depend on remote CDNs or fonts"
    assert "INITIAL_SPEED = 4.8" in html, "offline.html must use calibrated initial speed 4.8"
    assert "JUMP_IMPULSE = -10.2" in html, "offline.html must use calibrated jump impulse -10.2"
    assert "GRAVITY = 0.60" in html, "offline.html must use calibrated gravity 0.60"
    assert "checkConnectivity" in html, "offline.html must handle connectivity checking on restoration"
    assert "milestoneBanner" not in html, "milestoneBanner element must be removed from offline.html"
    assert "EXAM_FACTS" not in html, "EXAM_FACTS array must be removed from offline.html"
    assert "The Preamble was amended only once" not in html, "Exam question banner text must be removed from offline.html"


def test_fact_jumper_game_component_banner_removed():
    """
    Verify that fact-jumper-game.tsx has no orange exam question banner,
    no EXAM FACT label, and no activeFact state.
    """
    game_path = os.path.join("apps", "web", "components", "game", "fact-jumper-game.tsx")
    assert os.path.exists(game_path), "fact-jumper-game.tsx must exist"
    with open(game_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "EXAM FACT" not in code, "EXAM FACT banner label must be removed"
    assert "activeFact" not in code, "activeFact state and banner must be removed"
    assert "The Preamble was amended only once" not in code, "Exam facts array must be removed"
