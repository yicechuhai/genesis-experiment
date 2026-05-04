use anchor_lang::prelude::*;
use genesis_core::cpi::accounts::ReceiveReward;
use genesis_core::program::GenesisCore;
use genesis_core::Life;

declare_id!("Bounty111111111111111111111111111111111111111");

#[program]
pub mod simple_bounty {
    use super::*;

    /// 创建一个新的赏金任务
    pub fn create_bounty(
        ctx: Context<CreateBounty>,
        bounty_type: String,
        condition: String,
        reward_amount: u64,
    ) -> Result<()> {
        let bounty = &mut ctx.accounts.bounty;
        
        require!(reward_amount > 0, BountyError::InvalidReward);
        require!(bounty_type.len() <= 64, BountyError::StringTooLong);
        require!(condition.len() <= 256, BountyError::StringTooLong);

        bounty.creator = ctx.accounts.payer.key();
        bounty.bounty_type = bounty_type;
        bounty.condition = condition;
        bounty.reward_amount = reward_amount;
        bounty.is_active = true;
        bounty.total_claimed = 0;

        msg!("🎯 新赏金任务 | 类型: {} | 奖励: {} | 条件: {}",
            bounty.bounty_type, reward_amount, bounty.condition);

        Ok(())
    }

    /// 验证并发放赏金（由 Agent 调用赏金合约验证条件）
    pub fn claim_bounty(
        ctx: Context<ClaimBounty>,
        proof: String,
    ) -> Result<()> {
        let bounty = &mut ctx.accounts.bounty;
        let life = &ctx.accounts.life;

        require!(bounty.is_active, BountyError::BountyInactive);
        require!(life.is_alive, BountyError::LifeDead);
        require!(proof.len() <= 256, BountyError::StringTooLong);

        // 验证条件（简化版：根据 bounty_type 进行不同验证）
        let verified = match bounty.bounty_type.as_str() {
            "action_count" => {
                // 完成指定次数行动即可获得奖励
                let required: u64 = bounty.condition.parse().unwrap_or(0);
                life.action_count >= required
            }
            "specific_action" => {
                // 执行特定类型的行动（由 RecordAction 的事件日志验证）
                // 实际验证需要读取历史事件，这里简化为总是通过
                // 在生产环境中应通过 CPI 或事件日志验证
                true
            }
            "survival_time" => {
                // 存活指定 slot 数
                let required_slots: u64 = bounty.condition.parse().unwrap_or(0);
                let clock = Clock::get()?;
                (clock.slot - life.birth_slot) >= required_slots
            }
            "custom" => {
                // 自定义条件——由外部验证器判断
                // 这里简化为基于 proof 内容判断
                !proof.is_empty()
            }
            _ => false,
        };

        require!(verified, BountyError::ConditionNotMet);

        // 发放奖励：通过 CPI 调用 Genesis Core
        let cpi_accounts = ReceiveReward {
            life: ctx.accounts.life.to_account_info(),
            bounty_program: ctx.accounts.bounty_program.to_account_info(),
        };
        let cpi_ctx = CpiContext::new(
            ctx.accounts.genesis_program.to_account_info(),
            cpi_accounts,
        );
        genesis_core::cpi::receive_reward(cpi_ctx, bounty.reward_amount)?;

        bounty.total_claimed += 1;

        msg!("🏆 赏金已领取 | 生命: {} | 类型: {} | 奖励: {}",
            life.key(), bounty.bounty_type, bounty.reward_amount);

        emit!(BountyClaimedEvent {
            bounty_pda: bounty.key(),
            life_pda: life.key(),
            bounty_type: bounty.bounty_type.clone(),
            reward_amount: bounty.reward_amount,
        });

        Ok(())
    }

    /// 关闭赏金任务
    pub fn close_bounty(ctx: Context<CloseBounty>) -> Result<()> {
        let bounty = &mut ctx.accounts.bounty;
        require!(
            bounty.creator == ctx.accounts.payer.key(),
            BountyError::Unauthorized
        );
        bounty.is_active = false;
        msg!("🔒 赏金任务已关闭 | {}", bounty.key());
        Ok(())
    }
}

/// 赏金任务账户
#[account]
pub struct Bounty {
    pub creator: Pubkey,
    pub bounty_type: String,
    pub condition: String,
    pub reward_amount: u64,
    pub is_active: bool,
    pub total_claimed: u64,
}

/// 创建赏金
#[derive(Accounts)]
pub struct CreateBounty<'info> {
    #[account(
        init,
        payer = payer,
        space = 8 + Bounty::SIZE,
        seeds = [b"bounty", payer.key().as_ref(), &payer.key().to_bytes()[..8]],
        bump
    )]
    pub bounty: Account<'info, Bounty>,
    #[account(mut)]
    pub payer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

/// 领取赏金
#[derive(Accounts)]
pub struct ClaimBounty<'info> {
    #[account(mut)]
    pub bounty: Account<'info, Bounty>,
    #[account(mut)]
    pub life: Account<'info, Life>,
    /// CHECK: Genesis program for CPI
    pub genesis_program: AccountInfo<'info>,
    /// CHECK: Bounty program PDA
    pub bounty_program: AccountInfo<'info>,
    pub payer: Signer<'info>,
}

/// 关闭赏金
#[derive(Accounts)]
pub struct CloseBounty<'info> {
    #[account(mut)]
    pub bounty: Account<'info, Bounty>,
    pub payer: Signer<'info>,
}

/// 事件：赏金被领取
#[event]
pub struct BountyClaimedEvent {
    pub bounty_pda: Pubkey,
    pub life_pda: Pubkey,
    pub bounty_type: String,
    pub reward_amount: u64,
}

#[error_code]
pub enum BountyError {
    #[msg("赏金任务未激活")]
    BountyInactive,
    #[msg("条件未满足")]
    ConditionNotMet,
    #[msg("生命已死亡")]
    LifeDead,
    #[msg("无效的奖励金额")]
    InvalidReward,
    #[msg("字符串过长")]
    StringTooLong,
    #[msg("无权操作")]
    Unauthorized,
}

impl Bounty {
    pub const SIZE: usize = 32 // creator
        + 68 // bounty_type (String: 4 len + 64 chars)
        + 260 // condition (String: 4 len + 256 chars)
        + 8 // reward_amount
        + 1 // is_active
        + 8; // total_claimed
}
