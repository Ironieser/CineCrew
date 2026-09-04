const assetButtons = document.querySelectorAll('.asset-thumb');
const assetPreview = document.getElementById('assetPreview');
const assetLabel = document.getElementById('assetLabel');

assetButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    assetButtons.forEach((b) => b.classList.remove('active'));
    btn.classList.add('active');
    assetPreview.src = btn.dataset.src;
    assetLabel.textContent = btn.dataset.label;
  });
});

const comparisonCases = [
  {
    title: 'Movie 1 · "Superman"',
    plot: 'In a quiet barn, Jonathan unveils the alien spacecraft hidden beneath a tarp, forcing Clark to confront his true origins. He solemnly hands Clark a glowing alien key, explaining it holds the answer to the universe\'s greatest question. As Clark expresses fear and reluctance, Jonathan pulls him into a deeply emotional hug, encouraging his son to discover his true destiny.',
    advantage: 'Our method involves maintaining strict multi-scene character consistency and accurate narrative execution. Across different shots, unveiling the spaceship, handing over the glowing key, and the backlit hug, the model preserves the facial features and specific clothing details of both characters. Furthermore, it accurately translates key plot points into precise physical interactions and natural emotional expressions, visualising the script\'s core narrative.',
    baseline: 'videos/comparison/case1_ltx.mp4',
    ours: 'videos/comparison/case1_ours.mp4'
  },
  {
    title: 'TV Drama 2 · "Better Call Saul Ep1"',
    plot: 'In an oppressive black-and-white world, a nervous man living under the alias "Gene" mechanically kneads dough in a mall bakery. After work, he trudges through a snowstorm to his rundown apartment, sinks into a worn couch, and pushes an old VHS tape into the player. As the TV starts playing, the dark room is suddenly illuminated by a vibrant burst of color from the screen, and Gene sits bathed in the glow, silently watching his former, flamboyant self—Saul Goodman.',
    advantage: 'Our method is better at temporal consistency and physical realism, accurately generating complex fine-motor interactions such as kneading dough and inserting a VHS tape. Furthermore, it executes complex semantic prompts and dynamic lighting, reflecting the vibrant, colored TV glow onto the character\'s high-contrast black-and-white face.',
    baseline: 'videos/comparison/case2_ltx.mp4',
    ours: 'videos/comparison/case2_ours.mp4'
  },
  {
    title: 'TV Drama 3 · "Better Call Saul Ep2"',
    plot: 'In a solemn courtroom, an exhausted, sweating Saul passionately defends his young clients to a stern judge. To prove "nobody got hurt," he confidently turns on a CRT television, but it loudly broadcasts a chaotic video of figures grotesquely destroying a medical dummy. Met with the judge\'s disgusted glare in the dead-silent room, Saul\'s passion instantly drains away, leaving him to freeze in defeat and awkwardly adjust his cheap tie.',
    advantage: 'Our method is good at capturing emotional tension and fine-motor actions, rendering Saul\'s passionate defense, the judge\'s oppressive disgust, and the awkward physicality of Saul adjusting his tie. Furthermore, it adheres to the complex semantic prompt, maintaining visual fidelity and temporal coherence.',
    baseline: 'videos/comparison/case3_ltx.mp4',
    ours: 'videos/comparison/case3_ours.mp4'
  }
];

const comparisonTitle = document.getElementById('comparisonTitle');
const comparisonPlot = document.getElementById('comparisonPlot');
const comparisonAdvantage = document.getElementById('comparisonAdvantage');
const baselineVideo = document.getElementById('baselineVideo');
const oursVideo = document.getElementById('oursVideo');
const caseCounter = document.getElementById('caseCounter');
const caseSlider = document.getElementById('caseSlider');
const caseButtons = document.querySelectorAll('.case-btn');
const prevCase = document.getElementById('prevCase');
const nextCase = document.getElementById('nextCase');

let currentCase = 0;

function renderCase(index) {
  currentCase = index;
  const item = comparisonCases[index];
  comparisonTitle.textContent = item.title;
  comparisonPlot.textContent = item.plot;
  comparisonAdvantage.textContent = item.advantage;
  baselineVideo.src = item.baseline;
  oursVideo.src = item.ours;
  baselineVideo.load();
  oursVideo.load();
  caseCounter.textContent = `${index + 1} / ${comparisonCases.length}`;
  caseSlider.value = String(index);
  caseButtons.forEach((btn, idx) => {
    btn.classList.toggle('active', idx === index);
  });
}

caseButtons.forEach((btn) => {
  btn.addEventListener('click', () => renderCase(Number(btn.dataset.index)));
});

caseSlider.addEventListener('input', (e) => {
  renderCase(Number(e.target.value));
});

prevCase.addEventListener('click', () => {
  renderCase((currentCase - 1 + comparisonCases.length) % comparisonCases.length);
});

nextCase.addEventListener('click', () => {
  renderCase((currentCase + 1) % comparisonCases.length);
});

renderCase(0);
