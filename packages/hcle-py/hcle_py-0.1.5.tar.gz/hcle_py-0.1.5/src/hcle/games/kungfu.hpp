// src/hcle/games/smb1.hpp
#pragma once
#include "game_logic.hpp"

namespace hcle
{
    namespace games
    {

        class KungFuLogic : public GameLogic
        {
        public:
            KungFuLogic()
            {
                action_set = {
                    NES_INPUT_UP,
                    NES_INPUT_DOWN,
                    NES_INPUT_LEFT,
                    NES_INPUT_RIGHT,
                    NES_INPUT_B,
                    NES_INPUT_A,
                };
                // action_set.resize(256);
                // std::iota(action_set.begin(), action_set.end(), 0);
            }

            GameLogic *clone() const override { return new KungFuLogic(*this); }

        private:
            bool inGame() { return m_current_ram_ptr[MENU] != 0x00; }
            bool isActionable() { return m_current_ram_ptr[ACTION_STATE] == 0x02; }
            bool isDead() { return m_current_ram_ptr[DEAD] != 0x00; }
            bool inAttractMode() { return m_current_ram_ptr[ATTRACT] == 1; }

            static const int GAME_STATE = 0x0006;
            static const int ACTION_STATE = 0x51; // 2 when actionable, 1 when waitin in cutscene, 0 in menu
            static const int ATTRACT = 0x06B;
            static const int IN_PLAY = 0x0390;
            static const int HP = 0x04A6;
            static const int ACTIONABLE = 0x60;
            static const int MENU = 0x5C;
            static const int X_FINE = 0xD4;
            static const int X_LARGE = 0xA3;
            static const int FLOOR = 0x58;
            static const int DEAD = 0x038D;
            static constexpr int SCORE_ADDRS[] = {0x0535, 0x0534, 0x0533, 0x0532};

            int64_t score(const uint8_t *ram) const
            {
                int64_t total_score = 0;
                int64_t mult = 1;
                for (int addr : SCORE_ADDRS)
                {
                    total_score += static_cast<int64_t>(ram[addr]) * mult;
                    mult *= 10;
                }
                return total_score;
            }

            float scoreChange() const
            {
                return static_cast<float>(score(m_current_ram_ptr) - score(m_previous_ram.data()));
            }

            float xChange() const
            {
                int64_t change = static_cast<int64_t>(m_current_ram_ptr[X_FINE]) - static_cast<int64_t>(m_previous_ram[X_FINE]);
                if (std::abs(change) == 255)
                {
                    return -static_cast<float>(change) / 255.0f;
                }
                else if (std::abs(change) > 3)
                {
                    return 0.0f;
                }
                return static_cast<float>(change);
            }

            float hpChange() const
            {
                int64_t change = static_cast<int64_t>(m_current_ram_ptr[HP]) - static_cast<int64_t>(m_previous_ram[HP]);
                if (change > 0 || m_current_ram_ptr[HP] == 0)
                {
                    return 0.0;
                }
                return static_cast<float>(change);
            }

        public:
            bool isDone() override { return isDead(); }

            double getReward() override
            {
                if (inAttractMode())
                {
                    return 0.0;
                }

                double reward = -0.01; // Time penalty

                float x_reward = xChange() * 10;
                if (m_current_ram_ptr[FLOOR] % 2 == 0)
                {
                    reward -= x_reward;
                }
                else
                {
                    reward += x_reward;
                }

                reward += scoreChange() / 10.0;
                reward += hpChange();

                if (isDead())
                {
                    reward -= 10.0;
                }

                return reward / 1000.0;
            }
            void onStep() override
            {
                if (!has_backup_ && inGame() && isActionable())
                {
                    createBackup();
                }

                if (!isActionable())
                {
                    this->frameadvance(NES_INPUT_NONE);
                }

                if (!inGame())
                {
                    this->frameadvance(NES_INPUT_NONE);
                    this->frameadvance(NES_INPUT_START);
                }
            }
        };

    } // namespace games
} // namespace hcle