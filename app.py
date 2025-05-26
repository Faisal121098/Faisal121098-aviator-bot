import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

# Aviator Bot Logic with Smart Strategy and Profit Target
class AviatorBot:
    def __init__(self, data, base_bet=10, cashout_target=2.0, balance=1000, loss_streak_threshold=3, strategy="martingale", profit_target=None):
        self.data = data
        self.base_bet = base_bet
        self.cashout_target = cashout_target
        self.balance = balance
        self.loss_streak_threshold = loss_streak_threshold
        self.strategy = strategy
        self.profit_target = profit_target
        self.current_bet = base_bet
        self.logs = []
        self.loss_streak = 0
        self.starting_balance = balance

    def run(self):
        for i, row in self.data.iterrows():
            if self.profit_target and self.balance - self.starting_balance >= self.profit_target:
                break

            multiplier = row['Multiplier']

            if self.loss_streak >= self.loss_streak_threshold:
                self.logs.append({
                    'Round': i+1,
                    'Bet': 0,
                    'Cashout_Target': self.cashout_target,
                    'Crash_At': multiplier,
                    'Win': None,
                    'Profit': 0,
                    'Balance': self.balance,
                    'Note': 'Skipped due to loss streak'
                })
                self.loss_streak -= 1
                continue

            result = {'Round': i+1, 'Bet': self.current_bet,
                      'Cashout_Target': self.cashout_target,
                      'Crash_At': multiplier}

            if multiplier >= self.cashout_target:
                profit = self.current_bet * (self.cashout_target - 1)
                self.balance += profit
                result['Win'] = True
                result['Profit'] = profit
                self.loss_streak = 0
                if self.strategy == "martingale":
                    self.current_bet = self.base_bet
                elif self.strategy == "anti-martingale":
                    self.current_bet *= 2
            else:
                self.balance -= self.current_bet
                result['Win'] = False
                result['Profit'] = -self.current_bet
                self.loss_streak += 1
                if self.strategy == "martingale":
                    self.current_bet *= 2
                elif self.strategy == "anti-martingale":
                    self.current_bet = self.base_bet

            result['Balance'] = self.balance
            result['Note'] = ''
            self.logs.append(result)

            if self.balance <= 0:
                break

        return pd.DataFrame(self.logs)

# Streamlit UI
st.title("🛩️ Aviator Predictor Bot Simulator")

st.sidebar.header("Bot Settings")
base_bet = st.sidebar.number_input("Base Bet ($)", min_value=1, value=10)
cashout_target = st.sidebar.number_input("Cashout Target (x)", min_value=1.01, value=2.0)
starting_balance = st.sidebar.number_input("Starting Balance ($)", min_value=10, value=1000)
loss_streak_threshold = st.sidebar.number_input("Skip After X Losses", min_value=0, value=3)
strategy = st.sidebar.selectbox("Betting Strategy", ["martingale", "anti-martingale"])
profit_target = st.sidebar.number_input("Profit Target ($, optional)", min_value=0, value=0)

st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload Aviator Data (CSV with 'Multiplier' column)", type=["csv"])

df = None
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("Data uploaded successfully!")
else:
    st.info("No file uploaded. Using simulated data.")
    np.random.seed(42)
    multipliers = np.random.exponential(scale=2, size=1000)
    multipliers = np.clip(multipliers, 1.01, 100)
    df = pd.DataFrame(multipliers, columns=['Multiplier'])

if st.sidebar.button("Run Bot"):
    bot = AviatorBot(
        df,
        base_bet=base_bet,
        cashout_target=cashout_target,
        balance=starting_balance,
        loss_streak_threshold=loss_streak_threshold,
        strategy=strategy,
        profit_target=profit_target if profit_target > 0 else None
    )
    results = bot.run()

    st.subheader("📊 Simulation Results")
    st.dataframe(results.tail(10))

    st.markdown(f"**Final Balance:** ${results['Balance'].iloc[-1]:.2f}")
    
    fig, ax = plt.subplots()
    ax.plot(results['Round'], results['Balance'], marker='o', linestyle='-', color='green')
    ax.set_title("Balance Over Time")
    ax.set_xlabel("Round")
    ax.set_ylabel("Balance ($)")
    st.pyplot(fig)

    csv = results.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Download Results as CSV",
        data=csv,
        file_name='aviator_bot_results.csv',
        mime='text/csv'
    )
else:
    st.info("Configure your settings and click 'Run Bot' to begin simulation.")
