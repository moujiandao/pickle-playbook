import { useState } from 'react'
import { NET_Y, KITCHEN, COURT_W, describePosition, describeBallZone } from '../constants'

// Mock rally generator — mirrors the prototype's logic.
// Replace the fetch call below with the real API once backend is ready.
function generateMockRally(players, ball, mySide) {
  const meKey = mySide === 'left' ? 'my_left' : 'my_right'
  const partnerKey = mySide === 'left' ? 'my_right' : 'my_left'
  const me = players[meKey]
  const partner = players[partnerKey]
  const oppL = players.opp_left
  const oppR = players.opp_right

  const myPos = describePosition(me.x, me.y, 'my')
  const partnerPos = describePosition(partner.x, partner.y, 'my')
  const oppLPos = describePosition(oppL.x, oppL.y, 'opp')
  const oppRPos = describePosition(oppR.x, oppR.y, 'opp')

  const ballInKitchen = ball.y >= NET_Y && ball.y <= NET_Y + KITCHEN
  const bothOppsK = oppL.y >= NET_Y - KITCHEN - 2 && oppR.y >= NET_Y - KITCHEN - 2
  const oppLWide = oppL.x < COURT_W / 4
  const oppRWide = oppR.x > (COURT_W * 3) / 4
  const middleOpen = Math.abs(oppL.x - oppR.x) > 8
  const meAtBaseline = me.y > NET_Y + KITCHEN + 5

  if (ballInKitchen && ball.height === 'low') {
    return [
      {
        name: 'Cross-Court Dink',
        why: `Ball low in kitchen. Opponents ${bothOppsK ? 'both at kitchen' : 'mixed'}.`,
        rally: [
          { shot: 1, who: 'You', action: 'Soft cross-court dink to backhand side', result: 'Lands in opponent kitchen, unattackable' },
          { shot: 2, who: 'Opponent', action: `${oppLWide ? 'OPP L stretches' : 'OPP L'} dinks back down the line`, result: 'Returns to your side mid-height' },
          { shot: 3, who: 'You', action: middleOpen ? 'Speed up through middle gap' : 'Reset with cross-court dink', result: middleOpen ? 'Splits defenders — winner' : 'Maintain kitchen position' },
        ],
      },
      {
        name: 'Erne Attack',
        why: `You at ${myPos}. Opponent at ${mySide === 'left' ? oppLPos : oppRPos}.`,
        rally: [
          { shot: 1, who: 'You', action: 'Jump around post for erne volley', result: 'Sharp angle surprises opponent' },
          { shot: 2, who: 'Opponent', action: 'Scramble return — weak pop-up', result: 'Ball floats high' },
          { shot: 3, who: 'Your Partner', action: `Partner at ${partnerPos} puts away overhead`, result: 'Winner' },
        ],
      },
    ]
  }

  if (ball.height === 'high' && ball.speed === 'slow') {
    return [
      {
        name: 'Overhead to Feet',
        why: `High slow ball. ${bothOppsK ? 'Both at kitchen — target feet.' : 'Target closer opponent.'}`,
        rally: [
          { shot: 1, who: 'You', action: `Smash at ${bothOppsK ? 'gap between opponents' : "closer opponent's feet"}`, result: 'Hard and low' },
          { shot: 2, who: 'Opponent', action: 'Defensive block — soft float back', result: 'Pop-up mid-court' },
          { shot: 3, who: 'You', action: 'Step in, angled volley putaway', result: 'Winner to open court' },
        ],
      },
      {
        name: 'Deep Placement',
        why: `Less risky. ${oppRWide || oppLWide ? 'Sideline exposed.' : 'Target weaker player.'}`,
        rally: [
          { shot: 1, who: 'You', action: `Controlled overhead deep to ${oppRWide ? 'right' : 'left'} sideline`, result: 'Pushes opponent behind baseline' },
          { shot: 2, who: 'Opponent', action: 'Defensive lob or drive from deep', result: 'Returns deep but you hold' },
          { shot: 3, who: 'You', action: 'Drop into kitchen while they\'re deep', result: 'Forces sprint — you control point' },
        ],
      },
    ]
  }

  if (meAtBaseline && ball.speed === 'fast') {
    return [
      {
        name: 'Deep Block + Transition',
        why: `You're deep at ${myPos}. Fast ball incoming.`,
        rally: [
          { shot: 1, who: 'You', action: 'Block-return deep, sprint forward', result: 'Buys transition time' },
          { shot: 2, who: 'Opponent', action: `Opponent at ${oppLPos} drives or drops`, result: "You're now in transition zone" },
          { shot: 3, who: 'You', action: 'Volley drop into kitchen', result: 'Complete advance to kitchen' },
        ],
      },
      {
        name: 'Counter-Drive Down Line',
        why: `Opponent at ${mySide === 'left' ? oppLPos : oppRPos} may be out of position.`,
        rally: [
          { shot: 1, who: 'You', action: 'Redirect pace down the line', result: 'Uses their power against them' },
          { shot: 2, who: 'Opponent', action: 'Partner scrambles — weak return', result: 'Short ball' },
          { shot: 3, who: 'Your Partner', action: `Partner at ${partnerPos} attacks`, result: 'Put-away at kitchen' },
        ],
      },
    ]
  }

  return [
    {
      name: 'Third-Shot Drop',
      why: `You at ${myPos}, ball in ${describeBallZone(ball.y)}.`,
      rally: [
        { shot: 1, who: 'You', action: 'Soft drop into opponent kitchen', result: 'Lands softly, unattackable' },
        { shot: 2, who: 'Opponent', action: `Opponent at ${oppLPos} dinks back`, result: 'Dink to your side' },
        { shot: 3, who: 'You', action: 'Advance to kitchen, engage dink rally', result: 'Positioning equalized' },
      ],
    },
    {
      name: 'Drive + Crash',
      why: `Aggressive. ${middleOpen ? 'Middle gap open.' : 'Apply pressure.'}`,
      rally: [
        { shot: 1, who: 'You', action: `Drive ${middleOpen ? 'through middle' : 'at weaker opponent'}`, result: 'Forces quick reaction' },
        { shot: 2, who: 'Opponent', action: 'Block return — soft ball', result: 'You advance' },
        { shot: 3, who: 'You', action: 'Volley drop from transition', result: 'Crash to kitchen line' },
      ],
    },
    {
      name: 'Lob Over Backhand',
      why: `${bothOppsK ? 'Both pressed to net.' : 'Creates depth.'}`,
      rally: [
        { shot: 1, who: 'You', action: 'Topspin lob over backhand side', result: 'Sails over net player' },
        { shot: 2, who: 'Opponent', action: 'Chases — running overhead or reset', result: 'Off-balance' },
        { shot: 3, who: 'You', action: 'Attack weak return while advancing', result: 'Gain court advantage' },
      ],
    },
  ]
}

export function useAnalyze() {
  const [result, setResult] = useState(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState(null)

  async function analyze(players, ball, mySide) {
    setIsAnalyzing(true)
    setResult(null)
    setError(null)

    try {
      const apiUrl = import.meta.env.VITE_API_URL

      if (apiUrl) {
        // Real API call when backend is available
        const resp = await fetch(`${apiUrl}/api/analyze`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ my_side: mySide, players, ball }),
        })
        if (!resp.ok) throw new Error(`API error ${resp.status}`)
        setResult(await resp.json())
      } else {
        // Mock: simulate network latency
        await new Promise((r) => setTimeout(r, 1200))
        setResult(generateMockRally(players, ball, mySide))
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  return { result, setResult, isAnalyzing, error, analyze }
}
