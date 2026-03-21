/* PARTICLES */
const canvas = document.getElementById("bg");
const ctx = canvas.getContext("2d");

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let particles = [];

for (let i = 0; i < 100; i++) {
    particles.push({
        x: Math.random()*canvas.width,
        y: Math.random()*canvas.height,
        size: 2,
        speedX: Math.random()-0.5,
        speedY: Math.random()-0.5
    });
}

function animate() {
    ctx.clearRect(0,0,canvas.width,canvas.height);

    particles.forEach(p => {
        p.x += p.speedX;
        p.y += p.speedY;

        ctx.beginPath();
        ctx.arc(p.x,p.y,p.size,0,Math.PI*2);
        ctx.fillStyle = "#00ffd5";
        ctx.fill();
    });

    requestAnimationFrame(animate);
}

animate();

/* TYPING */
const text = "Deepfake Detection AI 🤖";
let i = 0;

function typing() {
    if (i < text.length) {
        document.getElementById("typing").innerHTML += text.charAt(i);
        i++;
        setTimeout(typing, 80);
    }
}

typing();