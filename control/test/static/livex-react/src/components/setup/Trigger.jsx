import React from 'react';
import Col from 'react-bootstrap/Col';
import { Container } from 'react-bootstrap';
import Form from 'react-bootstrap/Form';
import Row from 'react-bootstrap/Row';
import InputGroup from 'react-bootstrap/InputGroup';
import Button from 'react-bootstrap/Button';
import { TitleCard, WithEndpoint, useAdapterEndpoint, StatusBox } from 'odin-react';

import { checkNullNoDp } from '../../utils';

import { useState } from 'react';
import ButtonGroup from 'react-bootstrap/ButtonGroup';
import ToggleButton from 'react-bootstrap/ToggleButton';

const EndPointFormControl = WithEndpoint(Form.Control);
const EndPointButton = WithEndpoint(Button);

function Trigger() {

    const triggerEndPoint = useAdapterEndpoint('trigger', 'http://192.168.0.22:8888', 1000);
    const orcaEndPoint = useAdapterEndpoint('camera/cameras/0', 'http://192.168.0.22:8888', 1000);
    const furnaceEndPoint = useAdapterEndpoint('furnace', 'http://192.168.0.22:8888', 1000);
    const liveXEndPoint = useAdapterEndpoint('livex', 'http://192.168.0.22:8888', 1000);

    const [timeFrameValue, setTimeFrameValue] = useState('time');
    const timeFrameRadios = [
      { name: 'Time', value: 'time' },
      { name: 'Frames', value: 'frame'}
    ];

    return (
      <Container>
        <TitleCard title="Acquisition details">
        <Container>
        <Row>
          <Col>
            <Row>
              Measure acq. duration in:
              <ButtonGroup>
                {timeFrameRadios.map((radio, idx) => (
                  <ToggleButton
                    key={idx}
                    id={`radio-${idx}`}
                    type="radio"
                    variant='outline-primary'
                    name="timeFrameRadio"
                    value={radio.value}
                    checked={timeFrameValue === radio.value}
                    onChange={(e) => setTimeFrameValue(e.currentTarget.value)}>
                      {radio.name}
                    </ToggleButton>
                ))}
              </ButtonGroup>
            </Row>
            <Row className="mt-3">
              <InputGroup>
                <InputGroup.Text>
                  Duration (s)
                </InputGroup.Text>
                {timeFrameValue==='time' ? (
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/time"}
                    value={liveXEndPoint.data.acquisition?.time}
                    disabled={timeFrameValue === 'frame'}
                    style={{border: timeFrameValue==='time' ? '1px solid #00cc00' : undefined}}>
                  </EndPointFormControl>
                ) : (
                  <InputGroup.Text style={{ flex: 1 }}>
                    {liveXEndPoint.data.acquisition?.time}
                  </InputGroup.Text>
                )}
              </InputGroup>
            </Row>
          </Col>
          <Col>
            <TitleCard title="Furnace">
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/furnace"}
                    value={triggerEndPoint.data.furnace?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  {timeFrameValue==='frame' ? (
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frame_target"}
                    value={triggerEndPoint.data.furnace?.target}
                    disabled={timeFrameValue==='time'}
                    style={{border: timeFrameValue==='frame' ? '1px solid #00cc00' : undefined}}>
                  </EndPointFormControl>
                  ) : (
                    <InputGroup.Text style={{ flex: 1 }}>
                      {triggerEndPoint.data.furnace?.target}
                    </InputGroup.Text>
                  )}
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
          <Col>
            <TitleCard title="WideFOV">
              <Row>
                <InputGroup style={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%'
                  }}>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/widefov"}
                    value={triggerEndPoint.data.widefov?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  <InputGroup.Text style={{flex: 1}}>
                  {triggerEndPoint.data.widefov?.target}
                  </InputGroup.Text>
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
          <Col>
            <TitleCard title="NarrowFOV">
              <Row>
                <InputGroup
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    width: '100%'
                  }}>
                  <InputGroup.Text>
                    Freq. (Hz)
                  </InputGroup.Text>
                  <EndPointFormControl
                    endpoint={liveXEndPoint}
                    type="number"
                    fullpath={"acquisition/frequencies/narrowfov"}
                    value={triggerEndPoint.data.narrowfov?.frequency}>
                  </EndPointFormControl>
                </InputGroup>
              </Row>
              <Row>
                <InputGroup>
                  <InputGroup.Text>
                    Frame #
                  </InputGroup.Text>
                  <InputGroup.Text style={{flex: 1}}>
                  {triggerEndPoint.data.narrowfov?.target}
                  </InputGroup.Text>
                </InputGroup>
              </Row>
            </TitleCard>
          </Col>
        </Row>
        <Row className='mt-3'>
          <Col>
            <StatusBox as="span" label="reading">
                  {checkNullNoDp(furnaceEndPoint.data.tcp?.tcp_reading?.counter)}
            </StatusBox>
          </Col>
          <Col>
            <StatusBox label="Frame count">
              {checkNullNoDp(orcaEndPoint?.data[0]?.status.frame_number)}
            </StatusBox>
          </Col>
          </Row>

          <Row>
            <EndPointButton
              endpoint={liveXEndPoint}
              fullpath={"acquisition/start"}
              value={true}
              event_type="click"
              >
                start acquisition
            </EndPointButton>
          </Row>
          <Row>
            <EndPointButton
              endpoint={liveXEndPoint}
              fullpath={"acquisition/stop"}
              value={true}
              event_type="click"
              variant="danger"
              >
                stop acquisition
            </EndPointButton>
          </Row>
          <Row>
            <EndPointButton
            endpoint={triggerEndPoint}
            fullpath={"furnace/enable"}
            value={false}
            event_type="click">
              turn off the furnace timer
            </EndPointButton>
            <EndPointButton
            endpoint={triggerEndPoint}
            fullpath={"widefov/enable"}
            value={false}
            event_type="click">
              turn off the widefov timer
            </EndPointButton>
            <EndPointButton
            endpoint={triggerEndPoint}
            fullpath={"narrowfov/enable"}
            value={false}
            event_type="click">
              turn off the narrowfov timer
            </EndPointButton>
          </Row>
        </Container>
        </TitleCard>
      </Container>
    )
}

export default Trigger;

