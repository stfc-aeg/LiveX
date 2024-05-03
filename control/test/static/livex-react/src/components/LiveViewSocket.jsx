import React, { useState, useEffect, useCallback } from 'react';
import { TitleCard } from 'odin-react';
import { Row, Col } from 'react-bootstrap';
import { Form } from 'react-bootstrap';
import { Button } from 'react-bootstrap';

const colorEffects = [
  'autumn', 'bone', 'jet', 'winter', 'rainbow', 'ocean', 'summer', 'spring',
  'cool', 'hsv', 'pink', 'hot', 'parula', 'magma', 'inferno', 'plasma',
  'viridis', 'cividis', 'twilight', 'twilight_shifted', 'turbo', 'deepgreen'
];

function LiveViewSocket(props) {
    const {name}=props;

    const [width, setWidth] = useState(640);
    const [height, setHeight] = useState(480);
    const [colorEffect, setColorEffect] = useState('bone');
    const [imageData, setImageData] = useState(null);
    const [autoFetch, setAutoFetch] = useState(false);
    const [delay, setDelay] = useState(1000);

    const fetchImage = useCallback(async () => {
        try {
          const socket = new WebSocket('ws://192.168.0.31:9002');

          socket.addEventListener('open', () => {
            const requestData = {
              width,
              height,
              color_effect: colorEffect,
            };
            socket.send(JSON.stringify(requestData));
          });

          socket.addEventListener('message', (event) => {
            const blob = new Blob([event.data], { type: 'image/jpeg' });
            const imageURL = URL.createObjectURL(blob);
            setImageData(imageURL);
          });

          socket.addEventListener('error', (error) => {
            console.error('WebSocket error:', error);
          });

          return () => {
            socket.close();
          };
        } catch (error) {
          console.error('Error fetching image:', error);
        }
      }, [width, height, colorEffect]);

      useEffect(() => {
        let intervalId;

        if (autoFetch) {
          intervalId = setInterval(fetchImage, delay);
        }

        return () => {
          clearInterval(intervalId);
        };
      }, [autoFetch, delay, fetchImage]);

      return (
        <TitleCard title={`${name} preview`}>
        <Form>
          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">Width</Form.Label>
            <Col sm="10">
              <Form.Control
                type="number"
                value={width}
                onChange={(e) => setWidth(parseInt(e.target.value, 10))}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">Height</Form.Label>
            <Col sm="10">
              <Form.Control
                type="number"
                value={height}
                onChange={(e) => setHeight(parseInt(e.target.value, 10))}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">Delay (ms)</Form.Label>
            <Col sm="10">
              <Form.Control
                type="number"
                value={delay}
                onChange={(e) => setDelay(parseInt(e.target.value, 10))}
              />
            </Col>
          </Form.Group>

          <Form.Group as={Row} className="mb-3">
            <Form.Label column sm="2">Color Effect</Form.Label>
            <Col sm="10">
              <Form.Control
                as="select"
                value={colorEffect}
                onChange={(e) => setColorEffect(e.target.value)}>
                {colorEffects.map(effect => (
                  <option key={effect} value={effect}>{effect}</option>
                ))}
              </Form.Control>
            </Col>
          </Form.Group>
        <Row className="mt-3">
            <Col xs="6" className="d-flex justify-content-end">
                <Button onClick={fetchImage}>Get Single Image</Button>
            </Col>
            <Col xs="6">
                <Button onClick={() => setAutoFetch(!autoFetch)}>
                {autoFetch ? 'Stop Auto Fetch' : 'Start Auto Fetch'}
                </Button>
            </Col>
        </Row>
        {imageData && <img src={imageData} alt="Fetched" />}
        </Form>
      </TitleCard>
    )
}

export default LiveViewSocket;