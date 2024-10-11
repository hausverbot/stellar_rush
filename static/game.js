const roomName = JSON.parse(document.getElementById('room-name').textContent);

const gameSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/game/'
    + roomName
    + '/'
);

const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    parent: 'phaser-game',
    physics: {
        default: 'arcade',
        arcade: {
            gravity: {y: 300},
            debug: false
        }
    },
    scene: {
        preload: preload,
        create: create,
        update: update
    }
};


let GAME_READY = 0x01;
let GAME_RUNNING = 0x02;
let GAME_OVER = 0x03;



let GameData = {};

GameData.state = 0;
GameData.score = 0;
GameData.player_id = "";
GameData.movement = {};
GameData.movement.x = 0.0;
GameData.movement.y = 0.0;
GameData.movement.facing = "";

GameData.stars = {};
GameData.bombs = {};
GameData.players = {};

GameData.player = null;
GameData.score_text = null;
GameData.current_scene = null;

GameData.stars_group = {};
GameData.bombs_group = {};
GameData.cursors = {};
GameData.platforms = {};


let game = new Phaser.Game(config);

function preload() {
    this.load.image('sky', '../../static/assets/sky.png');
    this.load.image('ground', '../../static/assets/platform.png');
    this.load.image('star', '../../static/assets/star.png');
    this.load.image('bomb', '../../static/assets/bomb.png');
    this.load.spritesheet('dude', '../../static/assets/dude.png', { frameWidth: 32, frameHeight: 48 });
}

function create() {
    GameData.current_scene = this;
    this.add.image(400, 300, 'sky');
    GameData.platforms = this.physics.add.staticGroup();
    GameData.platforms.create(400, 568, 'ground').setScale(2).refreshBody();
    GameData.platforms.create(600, 400, 'ground');
    GameData.platforms.create(50, 250, 'ground');
    GameData.platforms.create(750, 220, 'ground');

    GameData.player = this.physics.add.sprite(100, 450, 'dude');
    GameData.player.setBounce(0.2);
    GameData.player.setCollideWorldBounds(true);

    this.anims.create({
        key: 'left',
        frames: this.anims.generateFrameNumbers('dude', { start: 0, end: 3 }),
        frameRate: 10,
        repeat: -1
    });

    this.anims.create({
        key: 'turn',
        frames: [{ key: 'dude', frame: 4 }],
        frameRate: 20
    });

    this.anims.create({
        key: 'right',
        frames: this.anims.generateFrameNumbers('dude', { start: 5, end: 8 }),
        frameRate: 10,
        repeat: -1
    });

    GameData.cursors = this.input.keyboard.createCursorKeys();

    GameData.stars_group = this.physics.add.group();
    GameData.bombs_group = this.physics.add.group();

    this.physics.add.collider(GameData.player, GameData.platforms);
    this.physics.add.collider(GameData.stars_group, GameData.platforms);
    this.physics.add.collider(GameData.bombs_group, GameData.platforms);
    this.physics.add.overlap(GameData.player, GameData.stars_group, collectStar, null, this);
    this.physics.add.collider(GameData.player, GameData.bombs_group, hitBomb, null, this);

    GameData.score_text = this.add.text(16, 16, 'Score: 0', { fontSize: '32px', fill: '#000' });

    GameData.players = this.physics.add.group();

    gameSocket.onopen = (e) =>{
        send_message("connect", {})
    }

    gameSocket.onmessage = (e) => {
        const data = JSON.parse(e.data);
        //console.debug("JSON Received: ", data);

        if (data.topic === 'init'){
            game_init(data);
        } else if(data.topic === "player_joined"){
            game_player_joined(data);
        } else if(data.topic === "player_left"){
            game_player_left(data);
        } else if(data.topic === "game_start"){
            game_start(data);
        } else if(data.topic === "next_round"){
            game_next_round(data);
        } else if(data.topic === "game_over"){
            game_over(data);
        } else if(data.topic === "player_movement"){
            game_player_movement(data);
        } else if(data.topic === "star_collected"){
            game_star_collected(data);
        } else if(data.topic === "bomb_hit"){
            game_bomb_hit(data);
        } else{
            console.error("Unknown topic received");
        }
    }
}



function game_init(data){
    GameData.player_id = data.player_id;
    GameData.state = data.game_state;
    //GameData.players = data.players;

    $.each(data.players, function(id, player) {
        console.debug('Spawning player:', player);
        if (id !== GameData.player_id){
            game_spawn_other_player(id, GameData.movement.x, GameData.movement.y);
        }
    });

    setInterval(function () {
        GameData.movement.player_id = GameData.player_id;
        send_message('movement', GameData.movement)
    }, 33);

    if (GameData.state === GAME_READY) {
        $('#start_button').attr('disabled', false);
    } else if (GameData.state === GAME_RUNNING) {
        $('#start_button').attr('disabled', true);
    }
}

function game_star_collected(data){
    let star = game_get_star(data.star_id);
    if (star) {
        star.disableBody(true, true);
    }
}

function game_spawn_stars(stars){
    $.each(stars, function(id, star) {
        console.debug('Spawning star:', star);
        let newStar = GameData.stars_group.create(star.x, star.y, 'star');
        newStar.setBounceY(Phaser.Math.FloatBetween(0.4, 0.8));
        newStar.star_id = star.id;
        GameData.stars[star.id] = newStar;
    });
}

function game_get_star(id){
    return GameData.stars[id];
}

function game_get_bomb(id){
    let bomb = GameData.bombs[id];
    console.log(bomb)
    return bomb
}

function game_spawn_bomb(bomb){
    let new_bomb = GameData.bombs_group.create(bomb.x, bomb.y, 'bomb', bomb.vx);
    new_bomb.setBounce(1);
    new_bomb.setCollideWorldBounds(true);
    new_bomb.setVelocity(bomb.vx, 20);
    new_bomb.allowGravity = true;
    new_bomb.bomb_id = bomb.id;
    GameData.bombs[bomb.id] = new_bomb;
    console.debug('Bomb created:', bomb.id);
}

function game_spawn_bombs(bombs){
    $.each(bombs, function(id, bomb) {
        let old_bomb = game_get_bomb(id);
        if (!old_bomb) {
            game_spawn_bomb(bomb);
        }
    });
}

function game_destroy_bomb(id){
    let bomb = game_get_bomb(id);
    if (bomb) {
        bomb.destroy();
        console.debug('Bomb destroyed:', id);
    }
}

function game_start(data){
    $('#start_button').attr('disabled', true);
    console.log('Game started with stars and bombs:', data.payload.stars, data.payload.bombs);
    game_spawn_bombs(data.payload.bombs);
    game_spawn_stars(data.payload.stars);
}

function game_delete_all_stars(){
        $.each(GameData.stars, function(id, star) {
        console.debug('Deleting star:', id);
        star.disableBody(true, true);
    });
}

function game_next_round(data){
    game_delete_all_stars();
    game_spawn_bombs(data.bombs);
    game_spawn_stars(data.stars);
}

function game_over(data){
    console.debug('Game over');
}

function game_bomb_hit(data){
    if (data.player_id !== GameData.player_id) {
        let player = game_get_player(data.player_id)
        if (player) {
            game_kill_player(data.player_id);
        }
        game_destroy_bomb(data.bomb_id);

    }
}

function game_player_movement(data){
    if (data.player_id !== GameData.player_id) {
        let player = GameData.players[data.player_id]//game_get_player(data.player_id);
        if (player) {
            player.setX(data.payload.x);
            player.setY(data.payload.y);
            player.anims.play(data.payload.facing, true);
        }
    }
}

function game_player_joined(data){
    let player = game_get_player(data.player_id);
    if (!player) {
        game_spawn_other_player(data.player_id, 100, 450);
    }
}

function game_player_left(data){
    let player = game_get_player(data.player_id);
    if (player) {
        player.destroy();
    }
}

function game_get_player(id){
    return GameData.players[id];
}

function game_spawn_other_player(id, x, y) {
    const player = GameData.current_scene.add.sprite(x, y, 'dude');
    player.player_id = id;
    player.setTint(Math.random()*0xFFFFFF);
    GameData.players[id] = player;
}

function game_kill_player(id){
    let player = game_get_player(id);
    player.setTint(0xff0000);
    player.anims.play('turn');
    setTimeout(() => {
        player.destroy();
    }, 100);
}


function update() {
    if (GameData.state === GAME_OVER) {
        return;
    }
    GameData.movement.x = GameData.player.x;
    GameData.movement.y = GameData.player.y;

    if (GameData.cursors.left.isDown) {
        GameData.player.setVelocityX(-160);
        GameData.player.anims.play('left', true);
        GameData.movement.facing = 'left';

    } else if (GameData.cursors.right.isDown) {
        GameData.player.setVelocityX(160);
        GameData.player.anims.play('right', true);
        GameData.movement.facing = 'right';

    } else {
        GameData.player.setVelocityX(0);
        GameData.player.anims.play('turn');
        GameData.movement.facing = 'turn';
    }

    if (GameData.cursors.up.isDown && GameData.player.body.touching.down) {
        GameData.player.setVelocityY(-330);
    }
}

function collectStar(player, star) {
    star.disableBody(true, true);
    GameData.score += 10;
    GameData.score_text.setText('Score: ' + GameData.score);

    send_message('collect_star', { star_id: star.star_id });
}

function hitBomb(player, bomb) {
    player.setTint(0xff0000);
    player.anims.play('turn');
    send_message('hit_bomb', { bomb_id: bomb.bomb_id });
    setTimeout(() => {
        player.destroy();
        bomb.destroy();
    }, 100);
}



function send_message(topic, payload) {
    gameSocket.send(JSON.stringify({
        'type': "game_event",
        'topic': topic,
        'player_id': GameData.player_id,
        'payload': payload
    }));
}

$( document ).ready(function() {
    console.log( "ready!" );
    $("#start_button").click(function () {
        send_message("start_game", {})
    })
});