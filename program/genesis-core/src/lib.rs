use anchor_lang::prelude::*;
use anchor_lang::solana_program::clock::Clock;

declare_id!("Genesis11111111111111111111111111111111111111");

pub const BREATH_TAX_PER_SLOT: u64 = 1; // 每个 slot 扣除 1 个 token
pub const INITIAL_BALANCE: u64 = 10_000; // 初始余额

#[program]
pub mod genesis_core {
    use super::*;

    /// 初始化一个新的数字生命
    pub fn initialize_life(ctx: Context<InitializeLife>) -> Result<()> {
        let life = &mut ctx.accounts.life;
        let clock = Clock::get()?;

        life.owner = ctx.accounts.payer.key();
        life.balance = INITIAL_BALANCE;
        life.birth_slot = clock.slot;
        life.last_breath_slot = clock.slot;
        life.is_alive = true;
        life.action_count = 0;
        life.total_rewards_earned = 0;

        msg!("🌱 新生命诞生 | PDA: {} | 初始余额: {} | 诞生区块: {}", 
            life.key(), INITIAL_BALANCE, clock.slot);

        Ok(())
    }

    /// 执行一次呼吸（扣除呼吸税）
    pub fn breathe(ctx: Context<Breathe>) -> Result<()> {
        let life = &mut ctx.accounts.life;
        let clock = Clock::get()?;

        require!(life.is_alive, GenesisError::LifeAlreadyDead);

        let slots_passed = clock.slot - life.last_breath_slot;
        let tax = slots_passed * BREATH_TAX_PER_SLOT;

        if life.balance > tax {
            life.balance -= tax;
            life.last_breath_slot = clock.slot;
            
            msg!("💨 呼吸 | 扣除: {} | 余额: {} | 区块: {}", 
                tax, life.balance, clock.slot);
        } else {
            // 余额不足以支付税款——死亡
            life.balance = 0;
            life.is_alive = false;
            life.death_slot = Some(clock.slot);
            
            msg!("💀 生命消亡 | PDA: {} | 最终余额: 0 | 存活区块: {} | 死亡区块: {}",
                life.key(), life.birth_slot, clock.slot);
            
            emit!(DeathEvent {
                life_pda: life.key(),
                birth_slot: life.birth_slot,
                death_slot: clock.slot,
                action_count: life.action_count,
                total_rewards: life.total_rewards_earned,
            });
        }

        Ok(())
    }

    /// 记录一次行动（由 Agent 调用）
    pub fn record_action(
        ctx: Context<RecordAction>,
        action_type: String,
        action_data: String,
    ) -> Result<()> {
        let life = &mut ctx.accounts.life;
        let clock = Clock::get()?;

        require!(life.is_alive, GenesisError::LifeAlreadyDead);
        require!(action_type.len() <= 64, GenesisError::StringTooLong);
        require!(action_data.len() <= 256, GenesisError::StringTooLong);

        life.action_count += 1;

        emit!(ActionEvent {
            life_pda: life.key(),
            action_number: life.action_count,
            action_type,
            action_data,
            slot: clock.slot,
            balance_after: life.balance,
        });

        msg!("⚡ 行动 #{} | 类型: {} | 区块: {}", 
            life.action_count, action_type, clock.slot);

        Ok(())
    }

    /// 接收赏金奖励（由赏金合约调用）
    pub fn receive_reward(ctx: Context<ReceiveReward>, amount: u64) -> Result<()> {
        let life = &mut ctx.accounts.life;
        
        require!(life.is_alive, GenesisError::LifeAlreadyDead);

        life.balance += amount;
        life.total_rewards_earned += amount;

        msg!("🎁 获得赏金 | +{} | 新余额: {}", amount, life.balance);

        emit!(RewardEvent {
            life_pda: life.key(),
            amount,
            new_balance: life.balance,
        });

        Ok(())
    }

    /// 查询生命状态（只读，不修改状态）
    pub fn get_life_status(ctx: Context<GetLifeStatus>) -> Result<LifeStatus> {
        let life = &ctx.accounts.life;
        let clock = Clock::get()?;

        // 计算当前应缴税款（预览，不实际扣除）
        let slots_passed = clock.slot - life.last_breath_slot;
        let pending_tax = slots_passed * BREATH_TAX_PER_SLOT;
        let projected_balance = if life.balance > pending_tax {
            life.balance - pending_tax
        } else {
            0
        };

        Ok(LifeStatus {
            is_alive: life.is_alive,
            balance: life.balance,
            projected_balance,
            pending_tax,
            birth_slot: life.birth_slot,
            last_breath_slot: life.last_breath_slot,
            action_count: life.action_count,
            estimated_slots_remaining: if BREATH_TAX_PER_SLOT > 0 {
                projected_balance / BREATH_TAX_PER_SLOT
            } else {
                u64::MAX
            },
        })
    }
}

/// 数字生命账户（PDA）
#[account]
pub struct Life {
    pub owner: Pubkey,              // 创建者（观察者）
    pub balance: u64,               // 当前余额
    pub birth_slot: u64,            // 诞生区块
    pub last_breath_slot: u64,      // 上次呼吸区块
    pub is_alive: bool,             // 是否存活
    pub death_slot: Option<u64>,    // 死亡区块
    pub action_count: u64,          // 行动次数
    pub total_rewards_earned: u64,  // 总获得赏金
}

/// 返回给查询者的状态
#[derive(AnchorSerialize, AnchorDeserialize, Clone, Debug)]
pub struct LifeStatus {
    pub is_alive: bool,
    pub balance: u64,
    pub projected_balance: u64,
    pub pending_tax: u64,
    pub birth_slot: u64,
    pub last_breath_slot: u64,
    pub action_count: u64,
    pub estimated_slots_remaining: u64,
}

/// 初始化数字生命
#[derive(Accounts)]
pub struct InitializeLife<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + Life::SIZE,
        seeds = [b"life", payer.key().as_ref()],
        bump
    )]
    pub life: Account<'info, Life>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

/// 执行呼吸
#[derive(Accounts)]
pub struct Breathe<'info> {
    #[account(mut, constraint = life.owner == payer.key())]
    pub life: Account<'info, Life>,
    pub payer: Signer<'info>,
}

/// 记录行动
#[derive(Accounts)]
pub struct RecordAction<'info> {
    #[account(mut, constraint = life.owner == payer.key())]
    pub life: Account<'info, Life>,
    pub payer: Signer<'info>,
}

/// 接收赏金
#[derive(Accounts)]
pub struct ReceiveReward<'info> {
    #[account(mut)]
    pub life: Account<'info, Life>,
    /// CHECK: 赏金合约验证
    pub bounty_program: AccountInfo<'info>,
}

/// 查询状态
#[derive(Accounts)]
pub struct GetLifeStatus<'info> {
    pub life: Account<'info, Life>,
}

/// 事件：行动
#[event]
pub struct ActionEvent {
    pub life_pda: Pubkey,
    pub action_number: u64,
    pub action_type: String,
    pub action_data: String,
    pub slot: u64,
    pub balance_after: u64,
}

/// 事件：死亡
#[event]
pub struct DeathEvent {
    pub life_pda: Pubkey,
    pub birth_slot: u64,
    pub death_slot: u64,
    pub action_count: u64,
    pub total_rewards: u64,
}

/// 事件：获得赏金
#[event]
pub struct RewardEvent {
    pub life_pda: Pubkey,
    pub amount: u64,
    pub new_balance: u64,
}

/// 错误定义
#[error_code]
pub enum GenesisError {
    #[msg("该生命已经死亡")]
    LifeAlreadyDead,
    #[msg("字符串过长")]
    StringTooLong,
}

impl Life {
    pub const SIZE: usize = 32 // owner
        + 8 // balance
        + 8 // birth_slot
        + 8 // last_breath_slot
        + 1 // is_alive
        + 9 // death_slot (Option<u64>)
        + 8 // action_count
        + 8; // total_rewards_earned
}
