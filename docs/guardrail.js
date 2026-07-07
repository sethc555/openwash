/* OpenWASH — the reuse-safety guardrail, ported to the browser.
 *
 * This is a FAITHFUL port of engine/safe_reuse.py + the die-off logic it calls
 * (engine/dieoff.py), with the constants copied verbatim from data/dieoff_kinetics.yaml
 * (the `ascaris` block). It exists so a field worker with only a browser can get the
 * SAME verdict the Python engine gives — no install, no terminal.
 *
 * HONESTY GUARANTEE: tests/parity.py runs a large battery of designs through BOTH this
 * file (via Node) and the Python engine and requires IDENTICAL verdicts, and checks that
 * these constants equal the YAML. If they ever diverge, the `web_parity` claim fails.
 * SPDX-License-Identifier: Apache-2.0
 */
;(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.OpenWASH = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ---- constants — copied verbatim from data/dieoff_kinetics.yaml (organisms.ascaris) ----
  var DATA = {
    TARGET_EGG: 1.0,                 // <=1 viable helminth egg / g TS (WHO 2006 Vol 4)
    DEFAULT_INITIAL_EGGS: 40,
    ECOLI_LIMIT: 1000,               // <1000 CFU/g TS (WHO 2006 Vol 4)
    EGG_LIMIT_CHILD: 0.1,
    storage_meta_k: 0.0042,          // meta_analysis.k_log10_per_day (Musaazi 2023, faeces/solid)
    storage_rule: [                  // ascaris.storage_rule — WHO 2006 Vol4 Table 4.5
      { temp: [2, 20],  need: [548, 730] },
      { temp: [20, 35], need: [365, 400] }
    ],
    ammonia: {                       // ascaris.ammonia_model
      threshold_mM: 20,
      nh3_saturation_mM: 250,
      k_coeff: 2.6e-4,               // k_coeff_log10_per_day_per_mM
      Q10: 5.0
      // NH3 fraction: f = 1/(1+10^(pKa-pH)); pKa = 2729.92/T_kelvin + 0.09018 (Emerson/Nordin)
    },
    thermal: {                       // ascaris.thermal_model
      min_temp_C: 50,
      const_ge_7pct: 1.317e8         // solids_ge_7pct_constant — 40 CFR 503.32(a)(3)
    },
    dose: {                          // ascaris.ammonia_model.dosing (Nordin 2009)
      self_buffer_pH: 9.0,
      reference_moisture_pct: 83,
      measured: [ { urea_pct: 1, total_mM: 441 }, { urea_pct: 2, total_mM: 675 } ],
      urine_alt_mM: [200, 280]       // stored/hydrolysed urine ~3–4 g N/L (Udert 2006)
    },
    routes: ['food_raw', 'food_processed', 'non_food', 'soil_only']
  };

  // ---- die-off primitives (port of engine/dieoff.py) ----
  function nh3_fraction(pH, tempC) {
    var T = tempC + 273.15;
    var pKa = 2729.92 / T + 0.09018;
    return 1.0 / (1.0 + Math.pow(10, pKa - pH));
  }
  function k_ammonia(tempC, nh3_mM) {           // log10/day; 0 below threshold; clamped at saturation
    if (nh3_mM < DATA.ammonia.threshold_mM) return 0.0;
    var nh3 = Math.min(nh3_mM, DATA.ammonia.nh3_saturation_mM);
    return DATA.ammonia.k_coeff * nh3 * Math.pow(DATA.ammonia.Q10, (tempC - 24) / 10.0);
  }
  function epa_thermal_days(tempC) {
    return DATA.thermal.const_ge_7pct / Math.pow(10, 0.14 * tempC);
  }
  function ascaris_rule(tempC, days) {
    for (var i = 0; i < DATA.storage_rule.length; i++) {
      var b = DATA.storage_rule[i];
      if (b.temp[0] <= tempC && tempC <= b.temp[1]) {
        return { band: b.temp[0] + '–' + b.temp[1] + '°C', need_days: b.need, meets: days >= b.need[0] };
      }
    }
    return null;
  }

  function v(status, reason, fix, detail) {
    return { status: status, reason: reason, fix: fix || null, detail: detail || null };
  }
  function g2(x) { return Number(x.toPrecision(2)).toString(); }   // ~ python %.2g for display

  // ---- the three screens (port of engine/safe_reuse.py) ----
  function screen_storage(tempC, days, initial) {
    initial = (initial == null) ? DATA.DEFAULT_INITIAL_EGGS : initial;
    if (initial <= 0) return v('UNKNOWN', 'initial egg load must be positive to screen a design.');
    var rule = ascaris_rule(tempC, days);
    var lr = DATA.storage_meta_k * days;
    var resid = initial * Math.pow(10, -lr);
    if (!rule) return v('UNKNOWN',
      'No sourced storage rule covers ' + tempC + '°C.',
      'Bring the material into a covered regime (raise temperature, or add urine/urea/ash to sanitise by ammonia), then re-check.');
    if (!rule.meets) {
      var need = rule.need_days[0];
      return v('UNSAFE',
        'Passive storage at ' + tempC + '°C needs ≥ ' + need + ' days (~' + Math.round(need / 30) +
          ' months) to reach ≤1 viable egg/g; you have ' + days + '.',
        'Store ≥ ' + need + ' days at this temperature — OR add urine/urea/ash (pH ≥9) to sanitise far faster, ' +
          'OR heat-compost ≥50°C. Deployed passive storage has under-performed in the field (Kumwenda 2019, Malawi), ' +
          'so treat this bound as a floor.',
        'model: ' + lr.toFixed(1) + ' log → ' + g2(resid) + ' eggs/g; rule band ' + rule.band + '.');
    }
    if (resid > DATA.TARGET_EGG) {
      return v('UNSAFE',
        'Storage ' + days + ' d at ' + tempC + '°C meets the WHO categorical rule band, but the die-off model still ' +
          'leaves ~' + g2(resid) + ' viable eggs/g (target ≤1); the conservative signal governs.',
        'Hold longer — the model clears ≤1 egg/g only past the rule-band floor — or add urine/urea/ash (pH ≥9), ' +
          'or heat-compost ≥50°C; then re-check.',
        'model: ' + lr.toFixed(1) + ' log → ' + g2(resid) + ' eggs/g; rule band ' + rule.band + '.');
    }
    return v('SAFE_SCREEN',
      'Storage ' + days + ' d at ' + tempC + '°C meets both the WHO categorical rule (needs ' +
        rule.need_days[0] + '–' + rule.need_days[1] + ' d) and the first-order model for ≤1 viable egg/g.',
      null,
      'model: ' + lr.toFixed(1) + ' log → ' + g2(resid) + ' eggs/g (assuming ~' + initial +
        ' eggs/g initial load — a heavier load needs longer); rule band ' + rule.band + '.');
  }

  function screen_ammonia(tempC, days, pH, total_mM, initial) {
    initial = (initial == null) ? DATA.DEFAULT_INITIAL_EGGS : initial;
    if (initial <= 0) return v('UNKNOWN', 'initial egg load must be positive to screen a design.');
    if (total_mM == null) return v('UNKNOWN',
      'Ammonia inactivation is driven by the actual ammonia DOSE, which pH alone cannot confirm — ash/lime can raise pH ' +
        'while adding little or no nitrogen.',
      'Measure total ammoniacal-N (NH3+NH4⁺) with a strip/kit (mg/L ÷ 14 ≈ mM) and re-check. Guide: hydrolysed ' +
        'urine / urea dosing reaches ~150–300 mM; lime-only reads near zero.');
    if (pH < 8.5) return v('UNKNOWN',
      'pH ' + pH + ' is too low for meaningful ammonia sanitisation.',
      'Add more urine/urea (adds nitrogen AND raises pH) to reach pH ≥9, then re-check.');
    var Tc = Math.min(tempC, 34.0);
    var nh3 = Math.min(nh3_fraction(pH, Tc) * total_mM, DATA.ammonia.nh3_saturation_mM);
    var k = k_ammonia(Tc, nh3);
    if (k <= 0) return v('UNKNOWN',
      'At your measured ' + total_mM + ' mM dose and pH ' + pH + ', uncharged NH3 (~' + Math.round(nh3) + ' mM) is below the ~' +
        DATA.ammonia.threshold_mM + ' mM threshold where ammonia inactivation works.',
      'Increase the urine/urea dose or pH; warmer material also raises the active fraction.');
    var cure = Math.max(Math.log10(initial / DATA.TARGET_EGG) / k, 2.0 / k);
    if (days >= cure) return v('SAFE_SCREEN',
      'At your measured ' + total_mM + ' mM dose, pH ' + pH + ', ' + tempC + '°C, ammonia clears Ascaris in ~' +
        Math.round(cure) + ' d; you held ' + days + '.',
      null,
      'NH3(aq) ≈ ' + Math.round(nh3) + ' mM, k ≈ ' + k.toFixed(3) + ' log/d (from your ' + total_mM + ' mM total ammoniacal-N).');
    return v('UNSAFE',
      'At your measured ' + total_mM + ' mM dose, pH ' + pH + ', ' + tempC + '°C, ammonia needs ~' + Math.round(cure) +
        ' d to clear Ascaris; you held ' + days + '.',
      'Hold the batch ≥ ' + Math.round(cure) + ' days (sealed, to retain ammonia), or add more urine/urea to raise the dose, or warm it.',
      'NH3(aq) ≈ ' + Math.round(nh3) + ' mM, k ≈ ' + k.toFixed(3) + ' log/d (from your ' + total_mM + ' mM total ammoniacal-N).');
  }

  function screen_thermal(tempC, days) {
    if (tempC < DATA.thermal.min_temp_C) return v('UNKNOWN',
      tempC + '°C is below the ≥50°C thermal regime; there is no robust mesophilic (40–50°C) helminth ' +
        'time–temperature curve in the evidence.',
      'Either reach and hold ≥50°C uniformly (turned pile), or treat it as ambient storage (store for the full ' +
        'categorical time) / ammonia amendment instead.');
    var req = epa_thermal_days(tempC);
    if (days >= req) return v('SAFE_SCREEN',
      'Holding ≥' + tempC + '°C for ' + days + ' d meets the EPA time–temperature requirement (~' + req.toFixed(1) + ' d).',
      null, 'Requires the WHOLE mass to reach temperature — turn the pile; edges lag.');
    return v('UNSAFE',
      'At ' + tempC + '°C the EPA law requires ~' + req.toFixed(1) + ' d of hold; you have ' + days + '.',
      'Hold ≥' + req.toFixed(1) + ' days at ' + tempC + '°C (or hotter for less time), turning to heat the whole mass.');
  }

  function assess_urine(tempC, months, route) {
    var need = route === 'food_raw' ? 6 : (route === 'food_processed' ? 1 : 0);
    var label = need === 6 ? '≥6 months (all crops)'
              : need === 1 ? '≥1 month (processed crops only)'
              : 'own-household / non-food use (no storage needed)';
    if (need > 0 && tempC < 20) return v('UNKNOWN',
      'WHO urine-storage times (' + label + ') assume ~20°C; at ' + tempC + '°C inactivation is slower and these ' +
        'times are not validated.',
      'Store at ~20°C or warmer for the required months, or extend the time and verify by measurement, or restrict to ' +
        'processed / non-food / own-household use.');
    if (months >= need) return v('SAFE_SCREEN',
      'Urine stored ' + months + ' mo at ~' + tempC + '°C meets WHO guidance for this route (' + label + ').',
      null, 'Urine’s pathogen risk is low; storage clears it. Keep it OUT of contact with faeces (that would reintroduce the full load).');
    return v('UNSAFE',
      'This route needs ' + label + '; you stored ' + months + ' mo.',
      'Store urine ≥' + need + ' months at ~20°C before using on this crop class, or use it only on processed/non-food ' +
        'crops, or restrict to the producing household.');
  }

  // ---- amendment-dose planner (how to get from UNSAFE to a plan) — port of safe_reuse.dose_plan ----
  function ammonia_cure_days(temp, total_mM, pH, initial) {
    initial = initial || DATA.DEFAULT_INITIAL_EGGS;
    var Tc = Math.min(temp, 34.0);
    var nh3 = Math.min(nh3_fraction(pH, Tc) * total_mM, DATA.ammonia.nh3_saturation_mM);
    var k = k_ammonia(Tc, nh3);
    if (k <= 0) return null;
    return Math.max(Math.log10(initial / DATA.TARGET_EGG) / k, 2.0 / k);
  }
  function dose_plan(temp) {
    var ph = DATA.dose.self_buffer_pH;
    var options = DATA.dose.measured.map(function (row) {
      var cure = ammonia_cure_days(temp, row.total_mM, ph);
      return { urea_pct: row.urea_pct, total_mM: row.total_mM, cure_days: (cure == null ? null : Math.round(cure)) };
    });
    return {
      recommend: 'Add 1–2% urea by wet weight (Nordin 2009 — a tested dose, not a guess). It self-raises ' +
        'pH to ~9 and reaches a sanitising ammonia dose in typical faeces.',
      at_temp_C: temp, options: options,
      urine_alt_mM: DATA.dose.urine_alt_mM, measure_threshold_mM: DATA.ammonia.threshold_mM,
      caveats: [
        'This is a PLANNING estimate — MEASURE total ammoniacal-N to confirm (Nordin reached 441–862 mM; ' +
          'you need well above the ~' + DATA.ammonia.threshold_mM + ' mM threshold), especially if the material ' +
          'is much drier or wetter than typical faeces (~' + DATA.dose.reference_moisture_pct + '% water).',
        'Ash or lime raise pH but add ~no nitrogen — use them WITH urea/urine, never instead.',
        'Keep it sealed at pH ≥9 to retain ammonia; colder material is BOTH slower and has less active NH₃ at the same pH.'
      ]
    };
  }

  // params: storage/thermal [temp, days]; ammonia [temp, days, pH, total_mM|null]; urine [temp, months]
  function assess(material, treatment, params, route) {
    if (DATA.routes.indexOf(route) < 0) return v('UNKNOWN',
      "Unrecognised reuse route '" + route + "'.",
      'Use one of: ' + DATA.routes.join(', ') + ' (raw-eaten crops are the strictest).');
    if (material === 'urine') return assess_urine(params[0], params[1], route);
    if (treatment === 'none') return v('UNSAFE',
      'Untreated material reused directly is a disease vector — raw excreta carries the full pathogen load (Ascaris eggs survive months).',
      'Sanitise before ANY reuse: ammonia (urine/urea/ash, pH ≥9), heat ≥50°C, or long storage.');
    if (treatment === 'storage') return screen_storage(params[0], params[1]);
    if (treatment === 'ammonia') return screen_ammonia(params[0], params[1], params[2], params[3]);
    if (treatment === 'thermal') return screen_thermal(params[0], params[1]);
    return v('UNKNOWN', "Unrecognised treatment '" + treatment + "'.", null);
  }

  // ---- verification plan (what a paired test kit must measure) — display only ----
  function verification_plan(material, treatment, params, route) {
    var steps = [];
    if (material === 'urine')
      steps.push(['① PROCESS (every batch)', 'urine was stored the required months with NO faecal contact',
        'a dated storage log + separation check', 'near-free']);
    else if (treatment === 'storage')
      steps.push(['① PROCESS (every batch)', 'the batch actually sat ≥ the required time at ≥' + params[0] + '°C',
        'log start/end dates + a min–max thermometer', 'a calendar + a cheap thermometer — near-free']);
    else if (treatment === 'ammonia')
      steps.push(['① PROCESS (every batch)', 'pH stayed ≥' + params[2] + ' and the measured dose was held sealed for the required days',
        'pH strips + ammonia (NH3/NH4) test strips + thermometer + a batch log', 'strips ~$0.10 each, thermometer once']);
    else if (treatment === 'thermal')
      steps.push(['① PROCESS (every batch)', 'the WHOLE mass reached ≥' + params[0] + '°C for the required days (centre lags — probe it)',
        'a probe/datalogger in the pile CENTRE, plus turning records', 'one $10–30 logger, reused']);
    steps.push(['② E. COLI (per batch, ~$3–5)', 'E. coli < ' + DATA.ECOLI_LIMIT + ' CFU/g — catches gross treatment failure',
      'field MPN test (Aquagenx CBT) or 3M Petrifilm; incubate ~24–48 h',
      '~$3–5/test, NO lab — but LOW E. coli does NOT clear helminths']);
    steps.push(['③ HELMINTH (periodic audit — the hard, BINDING test)',
      'viable Ascaris eggs < ' + DATA.TARGET_EGG.toFixed(0) + ' /g TS' + (route === 'food_raw' ? ' (tighten toward ' + DATA.EGG_LIMIT_CHILD + '/L if children are exposed)' : ''),
      'sieve → flotation → count under a microscope (a $50 USB/Foldscope works), THEN incubate 3–4 weeks to see if eggs are VIABLE',
      'slow (weeks) + skilled — do it per-N-batches or via a partner lab, not every batch']);
    return steps;
  }

  return {
    assess: assess, screen_storage: screen_storage, screen_ammonia: screen_ammonia,
    screen_thermal: screen_thermal, assess_urine: assess_urine, verification_plan: verification_plan,
    dose_plan: dose_plan, ammonia_cure_days: ammonia_cure_days,
    nh3_fraction: nh3_fraction, k_ammonia: k_ammonia, epa_thermal_days: epa_thermal_days,
    ascaris_rule: ascaris_rule, DATA: DATA
  };
});
