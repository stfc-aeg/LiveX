import { Col, Row, Form, FloatingLabel } from 'react-bootstrap';
import { TitleCard, WithEndpoint } from 'odin-react';
import { floatingInputStyle } from '../../utils';

const EndPointFormControl = WithEndpoint(Form.Control);

function FurnaceMeta(props) {
    const {furnaceEndPoint } = props;
    const {connectedDisable} = props;

    return (
      <TitleCard title={
        <Row>
          <Col xs={6} className="d-flex align-items-center" style={{fontSize:'1.3rem'}}>Furnace Settings</Col>
        </Row>
      }>
        <Col>
          <Row>
            <Col xs={6}>
              <FloatingLabel label="Max Setpoint">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={"max_setpoint"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
            <Col xs={6}>
              <FloatingLabel label="Max Setpoint Increase">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={"max_setpoint_increase"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
          </Row>
          <Row className="mt-3">
            <Col xs={6}>
              <FloatingLabel label="Upper Output Power Scalar">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={"pid_upper/output_scalar"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
            <Col xs={6}>
              <FloatingLabel label="Lower Output Power Scalar">
                <EndPointFormControl
                  endpoint={furnaceEndPoint}
                  fullpath={"pid_lower/output_scalar"}
                  disabled={connectedDisable}
                  style={floatingInputStyle}
                />
              </FloatingLabel>
            </Col>
          </Row>
        </Col>
          
      </TitleCard>
    )
}

export default FurnaceMeta;