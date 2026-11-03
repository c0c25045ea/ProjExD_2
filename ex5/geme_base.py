import os
import random
import sys
import math
import pygame
# ワーキングディレクトリを作業ファイルの場所に設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 定数定義
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60
TIME_LIMIT = 120  # 制限時間（秒）

# 色の定義 (RGB)
COLOR_BG = (50, 160, 50)       # 緑色（フィールド）
COLOR_PLAYER = (0, 100, 255)   # 青色（プレイヤー）
COLOR_ENEMY = (255, 50, 50)    # 赤色（敵）
COLOR_WHITE = (255, 255, 255)  # 白色
COLOR_RED = (200, 0, 0)        # 強調用赤
COLOR_SHOOTER_ENEMY = (160, 32, 240) # 紫色（シューター敵）
COLOR_DASH_ENEMY = (255, 255, 0)     # 黄色（ダッシュ敵）
COLOR_ENEMY_BULLET = (255, 0, 128)   # ピンク色（敵の弾）


class Player:
    """プレイヤーキャラクターの移動、HP、描画を管理するクラス"""

    def __init__(self, x: float, y: float) -> None:
        """プレイヤーの初期位置やステータスを設定する"""
        self.x: float = x
        self.y: float = y
        self.radius: int = 15
        self.speed: float = 4.0
        self.hp: int = 100
        self.max_hp: int = 100
        self.invincible_timer: int = 0  # 被弾後の無敵時間フレームカウンタ

    def update(self, keys: pygame.key.ScancodeWrapper) -> None:
        """キー入力を受けて移動処理を行い、画面外への逸脱を防ぐ"""
        dx: float = 0.0
        dy: float = 0.0

        # WASDキーによる入力判定
        if keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_s]:
            dy += 1.0
        if keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_d]:
            dx += 1.0

        # 斜め移動時の速度が速くならないように正規化（1 / √2 ≒ 0.7071）
        if dx != 0.0 and dy != 0.0:
            dx *= 0.7071
            dy *= 0.7071

        # 位置の更新
        self.x += dx * self.speed
        self.y += dy * self.speed

        # 画面外に出ないように制限
        if self.x - self.radius < 0:
            self.x = self.radius
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius

        if self.y - self.radius < 0:
            self.y = self.radius
        elif self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius

        # 無敵タイマーのカウントダウン
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

    def draw(self, screen: pygame.Surface) -> None:
        """プレイヤーを描画する（無敵時間中は点滅表現を行う）"""
        # 無敵時間中は点滅させる（5フレームごとに表示・非表示を切り替え）
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return

        pygame.draw.circle(screen, COLOR_PLAYER, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def get_pos(self) -> tuple[float, float]:
        """プレイヤーの現在座標を返す"""
        return (self.x, self.y)

    def get_hp(self) -> int:
        """プレイヤーの現在のHPを返す"""
        return self.hp

    def take_damage(self, amount: int) -> None:
        """ダメージを受け、無敵時間を付与する"""
        if self.invincible_timer == 0:
            self.hp -= amount
            if self.hp < 0:
                self.hp = 0
            self.invincible_timer = 60  # 1秒間（60フレーム）の無敵時間


class Enemy:
    """敵キャラクターの基本クラス"""

    def __init__(self, x: float, y: float) -> None:
        """敵の初期位置を設定する"""
        self.x: float = x
        self.y: float = y
        self.radius: int = 12
        self.speed: float = 2.2
        self.color: tuple[int, int, int] = COLOR_ENEMY

    def update(self, player_x: float, player_y: float) -> None:
        """プレイヤーの方向に向かって移動する"""
        dx: float = player_x - self.x
        dy: float = player_y - self.y
        distance: float = math.hypot(dx, dy)

        # プレイヤーに向かって単位ベクトルを掛けて移動
        if distance > 0:
            dx /= distance
            dy /= distance
            self.x += dx * self.speed
            self.y += dy * self.speed

    def draw(self, screen: pygame.Surface) -> None:
        """敵を描画する"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)

    def get_pos(self) -> tuple[float, float]:
        """敵の現在座標を返す"""
        return (self.x, self.y)


class EnemyBullet:
    """【追加機能】シューター敵が発射する弾クラス"""
    def __init__(self, x: float, y: float, target_x: float, target_y: float) -> None:
        self.x: float = x
        self.y: float = y
        self.radius: int = 5
        self.speed: float = 5.0
        dx: float = target_x - x
        dy: float = target_y - y
        dist: float = math.hypot(dx, dy)
        if dist > 0:
            self.vx: float = (dx / dist) * self.speed
            self.vy: float = (dy / dist) * self.speed
        else:
            self.vx, self.vy = 0.0, self.speed

    def update(self) -> None:
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen: pygame.Surface) -> None:
        pygame.draw.circle(screen, COLOR_ENEMY_BULLET, (int(self.x), int(self.y)), self.radius)

    def is_out_of_bounds(self) -> bool:
        return self.x < -20 or self.x > SCREEN_WIDTH + 20 or self.y < -20 or self.y > SCREEN_HEIGHT + 20


class ShooterEnemy(Enemy):
    """【追加機能】シュータータイプの敵クラス（一定距離を保ち弾を撃つ）"""
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.radius = 14
        self.speed = 1.5
        self.color = COLOR_SHOOTER_ENEMY
        self.shoot_timer: int = 0
        self.shoot_interval: int = 120  # 2秒ごとに発射

    def update_and_shoot(self, player_x: float, player_y: float) -> EnemyBullet | None:
        dx: float = player_x - self.x
        dy: float = player_y - self.y
        dist: float = math.hypot(dx, dy)

        if dist > 200:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed

        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return EnemyBullet(self.x, self.y, player_x, player_y)
        return None


class DashEnemy(Enemy):
    """【追加機能】ダッシュタイプの敵クラス"""
    def __init__(self, x: float, y: float) -> None:
        super().__init__(x, y)
        self.radius = 13
        self.speed = 1.2
        self.color = COLOR_DASH_ENEMY
        self.state: str = "NORMAL"
        self.timer: int = 0
        self.dash_vx: float = 0.0
        self.dash_vy: float = 0.0

    def update(self, player_x: float, player_y: float) -> None:
        dx: float = player_x - self.x
        dy: float = player_y - self.y
        dist: float = math.hypot(dx, dy)

        if self.state == "NORMAL":
            if dist > 0:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            if dist < 220:
                self.state = "CHARGING"
                self.timer = 30  # 0.5秒溜め
                if dist > 0:
                    self.dash_vx = (dx / dist) * 9.0
                    self.dash_vy = (dy / dist) * 9.0

        elif self.state == "CHARGING":
            self.timer -= 1
            if self.timer <= 0:
                self.state = "DASHING"
                self.timer = 25

        elif self.state == "DASHING":
            self.x += self.dash_vx
            self.y += self.dash_vy
            self.timer -= 1
            if self.timer <= 0:
                self.state = "NORMAL"

    def draw(self, screen: pygame.Surface) -> None:
        draw_color = COLOR_RED if (self.state == "CHARGING" and (self.timer // 3) % 2 == 0) else self.color
        pygame.draw.circle(screen, draw_color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, COLOR_WHITE, (int(self.x), int(self.y)), self.radius, 2)



class Game:
    """ゲーム全体の状態、時間、スコア、当たり判定を管理するクラス"""

    def __init__(self) -> None:
        """Pygameとゲーム変数を初期化する"""
        pygame.init()
        self.screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("SURVIVAL ARENA")
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.font: pygame.font.Font = pygame.font.SysFont(None, 36)
        self.large_font: pygame.font.Font = pygame.font.SysFont(None, 64)

        self.reset_game()

    def reset_game(self) -> None:
        """ゲームの状態を初期化またはリスタートする"""
        self.player: Player = Player(float(SCREEN_WIDTH / 2), float(SCREEN_HEIGHT / 2))
        self.enemies: list[Enemy] = []
        self.elapsed_frames: int = 0
        self.spawn_timer: int = 0
        self.game_state: str = "PLAYING"  # "PLAYING", "GAME_OVER", "CLEAR"

    def reset_game(self) -> None:
        self.player: Player = Player(float(SCREEN_WIDTH / 2), float(SCREEN_HEIGHT / 2))
        self.enemies: list[Enemy] = []
        self.enemy_bullets: list[EnemyBullet] = []  # ← この行を追加
        self.elapsed_frames: int = 0
        self.spawn_timer: int = 0
        self.game_state: str = "PLAYING"

    def run(self) -> None:
        """メインゲームループを実行する"""
        running: bool = True
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        # ゲームオーバーまたはクリア時にRキーでリスタート
                        if self.game_state in ["GAME_OVER", "CLEAR"]:
                            self.reset_game()

            keys = pygame.key.get_pressed()

            if self.game_state == "PLAYING":
                # プレイヤーの更新
                self.player.update(keys)

                # 時間経過のカウント
                self.elapsed_frames += 1
                survived_seconds = self.elapsed_frames // FPS
                if survived_seconds >= TIME_LIMIT:
                    self.game_state = "CLEAR"

                # 一定時間ごと（約1.5秒おごと）に敵を出現させる
                self.spawn_timer += 1
                if self.spawn_timer >= 90:
                    self.spawn_timer = 0
                    self.spawn_enemy()


                # 敵の更新
                px, py = self.player.get_pos()
                for enemy in self.enemies:
                    if isinstance(enemy, ShooterEnemy):

                        # シューター敵なら弾を発射する判定
                        bullet = enemy.update_and_shoot(px, py)
                        if bullet:
                            self.enemy_bullets.append(bullet)
                    else:
                        enemy.update(px, py)

                # 敵の弾の更新
                for bullet in self.enemy_bullets[:]:
                    bullet.update()
                    if bullet.is_out_of_bounds():
                        self.enemy_bullets.remove(bullet)


                # 当たり判定のチェック
                self.check_collisions()

                # HPが0になったらゲームオーバー
                if self.player.get_hp() <= 0:
                    self.game_state = "GAME_OVER"

            # 描画処理
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def spawn_enemy(self) -> None:
        """画面の上下左右の端からランダムに敵を生成する"""
        side = random.randint(0, 3)
        if side == 0:    # 上端
            x = random.randint(0, SCREEN_WIDTH)
            y = -20
        elif side == 1:  # 下端
            x = random.randint(0, SCREEN_WIDTH)
            y = SCREEN_HEIGHT + 20
        elif side == 2:  # 左端
            x = -20
            y = random.randint(0, SCREEN_HEIGHT)
        else:            # 右端
            x = SCREEN_WIDTH + 20
            y = random.randint(0, SCREEN_HEIGHT)

        # ★ ここで x と y が設定されたあとに敵を生成する
        rand_val = random.random()
        if rand_val < 0.50:      # 50%の確率で通常の敵
            new_enemy = Enemy(float(x), float(y))
        elif rand_val < 0.80:    # 30%の確率でシューター敵
            new_enemy = ShooterEnemy(float(x), float(y))
        else:                    # 20%の確率でダッシュ敵
            new_enemy = DashEnemy(float(x), float(y))

        self.enemies.append(new_enemy)

    def check_collisions(self) -> None:
        """プレイヤーとすべての敵の接触判定を行う"""
        px, py = self.player.get_pos()
        p_radius = self.player.radius

        for enemy in self.enemies:
            ex, ey = enemy.get_pos()
            e_radius = enemy.radius
            distance = math.hypot(px - ex, py - ey)

            # 円同士の当たり判定
            if distance < p_radius + e_radius:
                # （ダッシュ中の敵なら大ダメージ）
                if isinstance(enemy, DashEnemy) and enemy.state == "DASHING":
                    self.player.take_damage(35)
                else:
                    self.player.take_damage(20)

        # （敵の弾の当たり判定）
        for bullet in self.enemy_bullets[:]:
            distance = math.hypot(px - bullet.x, py - bullet.y)
            if distance < p_radius + bullet.radius:
                self.player.take_damage(15)  # 弾に当たると15ダメージ
                self.enemy_bullets.remove(bullet)

    def draw(self) -> None:
        """画面全体の描画を行う"""
        # 背景描画
        self.screen.fill(COLOR_BG)

        # キャラクター描画
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)

        # UI（HP、スコア、残り時間）の描画
        hp_text = self.font.render(f"HP: {self.player.get_hp()}/{self.player.max_hp}", True, COLOR_WHITE)
        self.screen.blit(hp_text, (20, 20))

        survived_seconds = self.elapsed_frames // FPS
        score_text = self.font.render(f"Score (Time): {survived_seconds}s", True, COLOR_WHITE)
        self.screen.blit(score_text, (330, 20))

        remaining_seconds = max(0, TIME_LIMIT - survived_seconds)
        time_text = self.font.render(f"Limit: {remaining_seconds}s", True, COLOR_WHITE)
        self.screen.blit(time_text, (730, 20))

        # ゲーム終了時のオーバーレイとメッセージ
        if self.game_state == "GAME_OVER":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            game_over_text = self.large_font.render("GAME OVER", True, COLOR_RED)
            restart_text = self.font.render("Press R to Restart | Press ESC to Quit", True, COLOR_WHITE)
            
            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        elif self.game_state == "CLEAR":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            clear_text = self.large_font.render("CLEAR!", True, (255, 255, 0))
            restart_text = self.font.render("Press R to Restart | Press ESC to Quit", True, COLOR_WHITE)
            
            self.screen.blit(clear_text, (SCREEN_WIDTH // 2 - clear_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()